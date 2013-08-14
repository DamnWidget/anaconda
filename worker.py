# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import time
import errno
import socket
import logging
import asyncore
import threading
import subprocess

import sublime

from Anaconda.anaconda_client import AsynClient
from Anaconda.utils import get_settings, get_traceback, project_name

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.WARNING)

WORKERS = {}
WORKERS_LOCK = threading.RLock()


class Worker(object):
    """Worker class that start the server and handle the function calls
    """

    _shared_state = {}

    def __init__(self, paths=None):
        self.__dict__ = Worker._shared_state
        if hasattr(self, 'initialized') and self.initialized is True:
            return

        self.reconnecting = False
        self.client = None
        self.json_server = None
        self.paths = paths

        self.initialized = True

    @property
    def port(self):
        """Get first available port
        """

        s = socket.socket()
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()

        return port

    def start(self):
        """Start this worker
        """

        try:
            with WORKERS_LOCK:
                window_id = sublime.active_window().id()
                if not window_id in WORKERS:
                    loop_map = {}
                    WORKERS[window_id] = {
                        'loop_map': loop_map, 'port': self.port
                    }

            worker = WORKERS[window_id]
            if self.reconnecting is True:
                worker['port'] = self.port

            self.start_json_server(worker['port'])

            while not self.server_is_active(worker['port']):
                time.sleep(0.01)

            timeout = get_settings(
                sublime.active_window().active_view(),
                'asyncore_socket_timeout', 0.1
            )
            worker['client'] = AsynClient(worker['port'], worker['loop_map'])
            worker['runner'] = threading.Thread(
                target=asyncore.loop,
                kwargs={'timeout': timeout, 'map': worker['loop_map']}
            )
            worker['runner'].start()
        except Exception as error:
            logging.error(error)
            logging.error(get_traceback())

    def start_json_server(self, port):
        """Starts the JSON server
        """

        if self.server_is_active(port):
            if self.server_is_healthy(port):
                return

            self.sanitize_server()
            return

        logger.info('Starting anaconda JSON server...')
        self.build_server(port)

    def server_is_active(self, port):
        """Checks if the server is already active
        """

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', port))
            s.close()
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

    def server_is_healthy(self, port):
        """Check if the server process is healthy
        """

        if self.json_server.poll() is None:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(('localhost', port))
                s.sendall(bytes('{"method": "check"}', 'utf8'))
                data = sublime.value_decode(s.recv(1024))
                s.close()
            except:
                return False

            return data == b'Ok'
        else:
            logger.error(
                'Something is using the port {} in your system'.format(
                    port
                )
            )
            return True

    def sanitize_server(self):
        """Disconnect all the clients and terminate the server process
        """

        worker = WORKERS[sublime.active_window().id()]
        cl = AsynClient(worker['port'], worker['loop_map'])
        worker['client'] = cl

    def build_server(self, port):
        """Create the subprocess for the anaconda json server
        """

        kwargs = {
            'cwd': os.path.dirname(os.path.abspath(__file__)),
            'bufsize': -1
        }
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kwargs['startupinfo'] = startupinfo

        script_file = os.path.join(
            os.path.dirname(__file__),
            'anaconda_server{}jsonserver.py'.format(os.sep)
        )

        try:
            view = sublime.active_window().active_view()
            python = get_settings(view, 'python_interpreter', 'python')
        except:
            python = 'python'

        args = [python, '-B', script_file,  '-p', project_name(), str(port)]
        if self.paths is not None:
            args.extend(['-e', ','.join(self.paths)])

        args.extend([str(os.getpid())])
        self.json_server = subprocess.Popen(args, **kwargs)

    def execute(self, callback, **data):
        """Execute the given method in the remote server
        """

        window_id = sublime.active_window().id()
        if not window_id in WORKERS:
            self.start()

        worker = WORKERS[window_id]
        client = worker.get('client')
        if client is not None:
            if not client.connected and not worker['runner'].is_alive():
                self.reconnecting = True
                self.start()
            else:
                client.send_command(callback, **data)


def plugin_unloaded():
    """Called directly from sublime on plugin unload
    """

    global WORKERS
    with WORKERS_LOCK:
        for worker in WORKERS.values():
            worker.get('client').close()

        WORKERS = {}
