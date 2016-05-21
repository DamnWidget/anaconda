
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import time
import shlex
import logging
import subprocess

from urllib.parse import parse_qs

from .helpers import project_name
from .vagrant import VagrantIPAddress
from .remoteworker import RemoteWorker, RemoteChecker
from .helpers import active_view, create_subprocess, get_settings

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.WARNING)


class VagrantProcesser(object):
    """Starts a new instance if the minserver into a vagrant guest
    """

    def __init__(self):
        self.last_error = {}
        self._process = None
        self._machine_up = False

    def is_healthy(self):
        """Checks if the server process is halthy
        """

        if get_settings(active_view(), 'jsonserver_debug', False):
            return True

        if self._process.poll() is not None:
            self.last_error = {
                'error': 'the minserver process is terminated in the guest',
                'recommendation': 'check your vagrant machine and config'
            }
            return False

        return True

    def start(self, worker):
        """Create the subprocess for the vagrant minserver process
        """

        # first check if we are operating in manual mode
        if worker.manual or self._up_already(worker):
            return True

        args, kwargs = self._prepare_arguments(worker.rc)
        self._process = create_subprocess(args, **kwargs)
        time.sleep(1)
        if self._process is None or self._process.poll() is not None:
            # we can't spawn the vagrant command. Not installed?
            output, error = self._process.communicate()
            if error == b'Connection to 127.0.0.1 closed.\r\n':
                return True
            self.last_error = {
                'error': (
                    'Anaconda can not spawn the `vagrant` application to '
                    'run `{}`.\n\nProcess output: {}\n'
                    'Process error: {}'.format(
                        ' '.join(args),
                        output.decode('utf8'),
                        error.decode('utf8').replace('\n', ' ')
                    )
                ),
                'recommendation': 'Check your vagrant installation/config'
            }
            return False

        return True

    def _up_already(self, worker):
        """Returns True if the minserv is running already on guest
        """

        try:
            s = worker._get_service_socket()
            s.close()
            worker.rc['manual'] = True
        except:
            return False

        return True

    def _compose_script_file(self, rc):
        """Compose the script file location using the CV context
        """

        target_os = rc.get('os', 'posix').lower()
        sep = '\\' if target_os == 'windows' else '/'
        shared_dir = rc.get(
            'shared', '/anaconda' if target_os == 'posix' else 'C:\\anaconda')

        return '{0}{1}anaconda_server{1}minserver.py'.format(shared_dir, sep)

    def _compose_extra_paths(self, rc):
        """Compose extra paths (if any) using the CV context
        """

        extra_paths = []
        try:
            rc['extra'].extend([])
        except AttributeError:
            logger.warning(
                'Your `extra` quwry option is a string with commas but '
                'we expect a list of `extras`'
            )
            extra_paths.extend(rc['extra'].split(','))
        except KeyError:
            pass
        else:
            extra_paths.extend(rc['extra'])

        extra_paths.extend(get_settings(active_view(), 'extra_paths', []))

        return extra_paths

    def _prepare_arguments(self, rc):
        """Prepare subprocess arguments
        """

        script_file = self._compose_script_file(rc)
        interpreter = rc.get('interpreter', 'python')
        paths = self._compose_extra_paths(rc)
        cmd = 'vagrant ssh {} -c "{}"'.format(
            rc['machine_id'],
            '{} {} -p {}{} {}'.format(
                interpreter,
                script_file,
                project_name(),
                " '{}'".format('-e ' + ','.join(paths) if paths else ' '),
                rc['port']
            )
        )

        kwargs = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE}
        return shlex.split(cmd, posix=os.name != 'nt'), kwargs


class VagrantChecker(RemoteChecker):
    """Implement specific vagrant remote worker checks
    """

    def __init__(self):
        super(VagrantChecker, self).__init__()

    def vc_check(self, worker):
        """Check the vagrant configuration
        """

        if worker.rc.get('network') is None:
            worker.rc['network'] = 'forwarded'

        if worker.rc['network'] == 'public' and 'dev' not in worker.rc:
            self.last_error = {
                'error': 'network is configured as public but no device is specified',  # noqa
                'recommendation': (
                    'Specify a network device using `&dev=device` or use '
                    'other network topology'
                )
            }
            return False

        if worker.rc['network'] == 'private' and 'address' not in worker.rc:
            self.last_error = {
                'error': (
                    'vagrant network configured as private but no '
                    'address has been supplied'
                ),
                'reocmmendation': (
                    'Add the address parameter to your vagrant URI or '
                    'change the network paramater to forwarded'
                )
            }
            return False

        interpreter = worker.rc.get('interpreter', 'python')
        try:
            subprocess.call([interpreter, '-V'])
        except FileNotFoundError:
            self.last_error = {
                'error': (
                    'mode is not set as manual but the configured python '
                    'interpreter {} path does not exists'
                ).format(interpreter),
                'recommendation': 'Use a valid python interpreter'
            }
            return False

        return True

    def check(self, worker):
        """Perform required checks to conclude if it's safe to operate
        """

        # if last error is not empty just return False
        if not not self.last_error:
            return False

        if not worker.manual and not worker.processer.is_healthy():
            self.last_error = worker.processer.last_error
            return False

        timeout = 0
        while not self._status(worker):
            if timeout >= 200:
                return False
            time.sleep(0.1)
            timeout += 1

        return True

    def _check_status(self, rc):
        """Check vagrant status and translate machine to ID
        """

        p = create_subprocess(
            ['vagrant', 'global-status'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if p is None:
            self.last_error = {
                'error': 'vagrant is not installed or is not in the path',
                'recommendation': 'Install vagrant or update your path'
            }
            return

        output, error = p.communicate()
        if error:
            self.last_error = {
                'error': error, 'recommendation': 'Check your instalation'
            }
            return

        found = False
        for line in output.splitlines()[2:]:
            if not line:
                continue

            if line.startswith(b'The'):
                break

            data = line.split()
            if not data:
                continue

            if data[1].decode('utf8') == rc['machine']:
                found = True
                rc['machine_id'] = data[0].decode('utf8')
                if data[3] != b'running':
                    self.last_error = {
                        'error': 'Vagrant machine is not running',
                        'recommendation': 'Start your vagrant machine'
                    }
                    return
                break

        if not found:
            self.last_error = {
                'error': 'Vagrant machine {} does not exists'.format(
                    rc['machine']),
                'recommendation': 'Start your vagrant machine'
            }

    def _prepare_connection_addr(self, rc):
        """Prepare the addr tuple to connect to the vagrant machine
        """

        host, port = None, rc['port']
        if rc['network'] == 'forwarded':
            host = 'localhost'
        elif rc['network'] == 'private':
            host = rc['address']
        elif rc['network'] == 'public':
            host = VagrantIPAddress(
                rc['directory'], rc['machine'], rc['dev']
            ).ip_address

        self._remote_addr = (host, int(port))


class VagrantWorker(RemoteWorker):
    """
    This class implements a local worker that connects to a instance of
    minserver that tuns in a specific vagrant box in the user machine.
    """

    def __init__(self, data):

        super(VagrantWorker, self).__init__(data, VagrantChecker(), VagrantProcesser())  # noqa

    def start(self):
        self.checker.vc_check(self)
        if not self.checker.last_error:
            self.checker._prepare_connection_addr(self.rc)
            self.checker._check_status(self.rc)

        return super(VagrantWorker, self).start()

    @property
    def manual(self):
        """Return True if this worker is set as manual
        """

        return self.rc.get('manual') is not None

    def _parse_uri_data(self, data):
        """
        Parses the URI for this vagrant environment
        Vagrant scheme examples: (scheme://user:pwd@machine:port?options)
            vagrant://default:1936?network=forwarded
            vagrant://ubuntu:1936?network=private&address=10.0.0.4
            vagrant://archlinux:8888?network=public&dev=eth1&shared=~/opt/anaconda  # noqa
            vagrant://default:8888?network=forwarded&extra=~/project_one&extra=~/project_two  # noqa
        """

        netloc = data['netloc']
        query = data['query']

        if '@' in netloc:
            left, netloc = netloc.split('@')
            self.rc['username'], self.rc['password'] = left.split(':')

        self.rc['machine'], self.rc['port'] = netloc.split(':')

        if query:
            options = parse_qs(query)
            for key, value in options.items():
                self.rc[key] = value if key in ['extra', 'pathmap'] else value[0]  # noqa

        self.rc['network'] = self.rc.get('network', 'forwarded')
        self.rc['interpreter'] = self.rc.get('interpreter', 'python')

        pathmap = {}
        for map_data in self.rc.get('pathmap', []):
            split_data = map_data.split(',')
            if len(split_data) != 2:
                logger.warning('pathmap corruption? -> {}'.format(map_data))
                continue

            local_path = os.path.expanduser(os.path.expandvars(split_data[0]))
            remote_path = os.path.expanduser(os.path.expandvars(split_data[1]))
            pathmap[local_path] = remote_path

        self.rc['pathmap'] = pathmap
