# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import time
import errno
import socket
import random
import logging
import threading

import sublime

from .jsonclient import AsynClient
from .decorators import auto_project_switch
from .vagrant import VagrantStatus, VagrantIPAddress
from .builder.python_builder import AnacondaSetPythonBuilder
from .helpers import (
    get_settings, get_traceback, project_name, create_subprocess, active_view
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.WARNING)

WORKERS = {}
WORKERS_LOCK = threading.RLock()
LOOP_RUNNING = False


class BaseWorker(object):
    """Base class for different worker interfaces
    """

    def __init__(self):
        self.available_port = None
        self.reconnecting = False
        self.green_light = True
        self.last_error = None
        self.process = None
        self.client = None

    @property
    def port(self):
        """This method hast to be reimplementted
        """

        raise RuntimeError('This method must be reimplemented')

    @property
    def hostaddr(self):
        """Always returns localhost
        """

        return 'localhost'

    def start_json_server(self):
        """Starts the JSON server
        """

        if self.server_is_active():
            if self.server_is_healthy():
                return

            self.sanitize_server()
            return

        logger.info('Starting anaconda JSON server...')
        self.build_server()

    def server_is_active(self):
        """Checks if the server is already active
        """

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.05)
            s.connect((self.hostaddr, self.available_port))
            s.close()
        except socket.timeout:
            return False
        except socket.error as error:
            if error.errno == errno.ECONNREFUSED:
                return False
            else:
                logger.error(
                    'Unexpected error in `server_is_active`: {}'.format(error)
                )
                return False
        else:
            return True

    def server_is_healthy(self):
        """Checks if the server process is healthy
        """

        if get_settings(active_view(), 'jsonserver_debug', False) is True:
            return True

        if self.process.poll() is None:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((self.hostname, self.available_port))
                s.sendall(bytes('{"method": "check"}', 'utf8'))
                data = sublime.value_decode(s.recv(1024))
                s.close()
            except:
                return False

            return data == b'Ok'
        else:
            logger.error(
                'Something is using the port {} in your system'.format(
                    self.available_port
                )
            )
            return False

    @auto_project_switch
    def _execute(self, callback, **data):
        """Execute the given method in the remote server
        """

        self.client.send_command(callback, **data)


class LocalWorker(BaseWorker):
    """This worker is used with local interpreter
    """

    @property
    def port(self):
        """Get the first available port
        """

        if get_settings(active_view(), 'jsonserver_debug', False) is True:
            return get_settings(active_view(), 'jsonserver_debug_port', 9999)

        s = socket.socket()
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()

        return port

    def start(self):
        """Start this LocalWorker
        """

        if sublime.active_window().project_data():
            for build_system in sublime.active_window().project_data().get(
                    'build_systems', []):
                if build_system['name'] == 'Anaconda Python Builder':
                    break

            python_interpreter = get_settings(
                active_view(), 'python_interpreter')

            AnacondaSetPythonBuilder().update_interpreter_build_system(
                python_interpreter
            )
        if (sublime.active_window().project_data() and not
                sublime.active_window().project_data().get('build_systems')):
            python_interpreter = get_settings(
                active_view(), 'python_interpreter'
            )

            AnacondaSetPythonBuilder().update_interpreter_build_system(
                python_interpreter
            )

        if not self.available_port:
            self.available_port = self.port

        try:
            if self.reconnecting is True:
                self.available_port = self.port

            self.start_json_server()

            timeout = 0  # Wait for max 1 second.
            while timeout < 100 and not self.server_is_active() and self.green_light:  # noqa
                time.sleep(0.01)
                timeout += 1

            if self.green_light:
                self.client = AsynClient(self.available_port)
        except Exception as error:
            logging.error(error)
            logging.error(get_traceback())

    def sanitize_server(self):
        """Disconnect all the clients and terminate the server process
        """

        if self.client is not None:
            self.client.close()
            self.process.kill()
            self.start_json_server()

    def build_server(self):
        """Create the subprocess for the anaconda json server
        """

        script_file = os.path.join(
            os.path.dirname(__file__), os.pardir,
            'anaconda_server', 'jsonserver.py'
        )

        view = sublime.active_window().active_view()
        paths = [os.path.expanduser(p) for p
                 in get_settings(view, 'extra_paths', [])]
        try:
            paths.extend(sublime.active_window().folders())
        except AttributeError:
            sublime.error_message(
                'Your `extra_paths` configuration is a string but we are '
                'expecting a list of strings.'
            )
            paths = paths.split(',')
            paths.extend(sublime.active_window().folders())

        try:
            view = sublime.active_window().active_view()
            python = get_settings(view, 'python_interpreter', 'python')
            python = os.path.expanduser(python)
            if '$VIRTUAL_ENV' in python:
                if 'VIRTUAL_ENV' in os.environ:
                    python = python.replace(
                        '$VIRTUAL_ENV', os.environ.get('VIRTUAL_ENV'))
                else:
                    logging.info(
                        'WARNING: your anaconda configured python interpreter '
                        'is {} but there is no $VIRTUAL_ENV key in your '
                        'environment, fallin back to `python`.'.format(
                            get_settings(view, 'python_interpreter', 'python')
                        )
                    )
                    python = 'python'
        except:
            python = 'python'

        self.project_name = project_name()
        args = [
            python, '-B', script_file, '-p',
            self.project_name, str(self.available_port)
        ]
        if paths:
            for path in paths[:]:
                # hopefully fixes #341
                if not os.path.exists(path):
                    paths.remove(path)
            args.extend(['-e', ','.join(paths)])

        args.extend([str(os.getpid())])
        kwargs = {}
        if (
            len(sublime.active_window().folders()) > 0 and
            os.path.exists(sublime.active_window().folders()[0])
        ):
            kwargs['cwd'] = sublime.active_window().folders()[0]
        self.process = create_subprocess(args, **kwargs)
        if self.process is None:
            # we can't spawn a new process for jsonserver. Wrong config?
            self.green_light = False
            example = '/usr/bin/python'
            if os.name == 'nt':
                example = 'C:\Python27\python.exe'

            if random.randrange(10) == 4:
                sublime.error_message(
                    'Anaconda can not spawn a new process with your current '
                    'configured python interpreter ({}), make sure your '
                    'interpreter is a valid binary and is in your PATH or use '
                    'an absolute route to it, for example: {}'.format(
                        python, example
                    )
                )
        else:
            self.green_light = True


class RemoteWorker(BaseWorker):
    """This worker is used with non local machine interpreters
    """

    def __init__(self):
        super(RemoteWorker, self).__init__()
        self.config = active_view().settings().get('vagrant_environment')
        self.check_config()
        self.available_port = self.port
        self.checked = False
        self.check_status()
        self.support = True

    @property
    def port(self):
        """Return the right port for the given vagrant configuration
        """

        return self.config['network'].get('port', 19360)

    @property
    def hostaddr(self):
        """Get the right hostname for the guest machine
        """

        if self.config['network']['mode'] == 'forwarded':
            return 'localhost'

        if self.config['network'].get('address') is not None:
            return self.config['network']['address']

        return VagrantIPAddress(
            self.config['directory'], self.config['machine'],
            self.config['network'].get('interface', 'eth1')
        ).ip_address

    def start(self):
        """Start the jsonserver in the remote guest machine
        """

        if self.support is False:
            sublime.error_message(
                'Anaconda: vagrant support seems to be deactivated, that '
                'means that there were some problem with the configuration '
                'or maybe previous attempts to start a vagrant environemnt '
                'just failed. Did you forget to run command palette '
                '\'Anaconda: Vagrant activate\' after fix some problem?'
            )
            self.support = False
            return

        if not os.path.exists(os.path.expanduser(self.config['directory'])):
            sublime.error_message(
                '{} does not exists!'.format(self.config['directory'])
            )
        else:
            while not self.server_is_active():
                if self.support is not True:
                    return
                time.sleep(0.01)

            self.client = AsynClient(self.available_port, host=self.hostaddr)

    def check_config(self):
        """Check the vagrant project configuration
        """

        success = True
        if not self.config.get('directory') or not self.config.get('network'):
            success = False

        if self.config['network'].get('mode') is None:
            success = False

        if success is False:
            sublime.error_message(
                'Anaconda has detected that your vagrant_environment config '
                'is not valid or complete. Please, refer to https://'
                'github.com/DamnWidget/anaconda/wiki/Vagrant-Environments\n\n'
                'You may need to execute command palette \'Anaconda: '
                'Vagrant activate\' to re-activate anaconda  vagrant support'
            )
            self.support = False

        return success

    def check_status(self):
        """Check vagrant status
        """

        def status(result):
            success, running = result
            if not success:
                logging.error('Anaconda: {}'.format(running.decode('utf8')))
                self.support = False
                self.checked = True
            else:
                if not running:
                    self.support = False
                    logging.error('Anaconda: Vagrant machine is not running')
                    self.checked = True
                else:
                    self.checked = True

        VagrantStatus(
            status, self.config['directory'],
            self.config.get('machine', 'default')
        )
        while not self.checked:
            time.sleep(0.01)


class Worker(object):
    """Worker class that start the server and handle the function calls
    """

    _shared_state = {}

    def __init__(self):
        self.__dict__ = Worker._shared_state

    def vagrant_is_active(self):
        """Determines if vagrant is active for this project
        """

        return active_view().settings().get('vagrant_environment') is not None

    def execute(self, callback, **data):
        """Execute the given method remotely and call the callback with result
        """

        window_id = sublime.active_window().id()
        with WORKERS_LOCK:
            if window_id not in WORKERS:
                try:
                    if self.vagrant_is_active():
                        WORKERS[window_id] = RemoteWorker()
                    else:
                        WORKERS[window_id] = LocalWorker()
                except Exception as error:
                    logging.error(error)
                    logging.error(get_traceback())

        worker = WORKERS[window_id]
        if worker.client is not None:
            if not worker.client.connected:
                worker.reconnecting = True
                worker.start()
            else:
                worker._execute(callback, **data)
        else:
            worker.start()
