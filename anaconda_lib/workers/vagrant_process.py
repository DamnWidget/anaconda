
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import time
import shlex
import socket
import subprocess

from ..logger import Log
from ..helpers import create_subprocess
from ..helpers import debug_enabled, active_view, get_settings


class VagrantProcess(object):
    """Starts a new instance of the minserver into a vagrant guest
    """

    def __init__(self, interpreter):
        self.interpreter = interpreter
        self._process = None
        self.errpr = ''
        self.tip = ''

    @property
    def healthy(self):
        """Checks if the vagrant process is healthy
        """

        if debug_enabled:
            return True

        if self._process.poll() is not None:
            self.error = 'the minserver process is terminated in the guest'
            self.tip = 'check your vagrant machine and configuration'
            return False

        return True

    def start(self):
        """Create the subprocess for the vagrant minserver process
        """

        # first check if we are operating manual mode or server is up
        if self.interpreter.manual is not None or self._up_already():
            return True

        args, kwargs = self._prepare_arguments()
        self._process = create_subprocess(args, **kwargs)
        time.sleep(1)  # give it some time
        if self._process is None or self._process.poll() is not None:
            # we can't spawn the vagrant command. Not installed? Running?
            output, error = self._process.communicate()
            if error == b'Connection to 127.0.0.1 closed.\r\n':
                return True  # probably the minserver is running already
            self.error = (
                'Anaconda can not spawn the `vagrant` application to run `{}` '
                '\n\nProcess output: {}\nProcess error: {}'.format(
                    ' '.join(args),
                    output.decode('utf8'),
                    error.decode('utf8').replace('\n', ' ')
                )
            )
            self.tip = 'Check your vagrant installation/configuration'
            return False

        return True

    def _up_already(self):
        """Return True if the minserver is running already on guest
        """

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((self.interpreter.host, self.interpreter.port))
            s.close()
            self.interpreter.manual = True
        except:
            return False

        return True

    def _prepare_arguments(self):
        """Prepare subprocess arguments
        """

        script_file = self._compose_script_file()
        paths = self._compose_extra_paths()
        cmd = 'vagrant ssh {} -c "{}"'.format(
            self.interpreter.machine_id,
            '{} {} -p {}{} {}'.format(
                self.interpreter.interpreter,
                script_file,
                self.interpreter.project_name,
                " '{}'".format('-e ' + ','.join(paths) if paths else ' '),
                self.interpreter.port
            )
        )

        kwargs = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE}
        return shlex.split(cmd, posix=os.name != 'nt'), kwargs

    def _compose_script_file(self):
        """Compose the script file location using the interpreter context
        """

        target_os = self.interpreter.os
        target_os = 'posix' if target_os is None else target_os.lower()
        sep = '\\' if target_os == 'windows' else '/'
        shared = self.interpreter.shared
        if shared is None:
            shared = '/anaconda' if target_os == 'posix' else 'C:\\anaconda'

        return '{0}{1}anaconda_server{1}minserver.py'.format(shared, sep)

    def _compose_extra_paths(self):
        """Compose extra paths (if any) using the CV context
        """

        extra_paths = []
        try:
            self.interpreter.extra.extend([])
        except AttributeError:
            if self.interpreter.extra is not None:
                Log.warning(
                    'Your `extra` query option is a string but a list '
                    'was expected'
                )
                extra_paths.extend(self.interpreter.extra.split(','))
        else:
            extra_paths.extend(self.interpreter.extra)

        extra_paths.extend(get_settings(active_view(), 'extra_paths', []))
        return extra_paths
