
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os

from ..helpers import create_subprocess
from ..helpers import debug_enabled, active_view


class LocalProcess(object):
    """Starts a new local instance of the JsonServer
    """

    def __init__(self, interpreter):
        self.interpreter = interpreter
        self._process = None
        self.error = ''
        self.tip = ''

    @property
    def healthy(self):
        """Checks if the jsonserver process is healthy
        """

        if debug_enabled(active_view()):
            # if debug is active, the process is hadnled manually
            return True

        if self._process.poll() is not None:
            self.error = 'the jsonserver process is terminated'
            self.tip = 'check your operating system logs'
            return False

        return True

    def start(self):
        """
        Create the subprocess that start the anaconda JsonServer process
        using the configured Python Interpreter
        """

        if debug_enabled(active_view()):
            # if we are in debug mode the JsonServer is handled manually
            return True

        args, kwargs = self.interpreter.arguments
        self._process = create_subprocess(args, **kwargs)
        if self._process is None:
            # we can't spawn a new process for jsonserver, Wrong config?
            self._set_wrong_config_error()
            return False

        return True

    def stop(self):
        """Stop the current process
        """

        if self._process is not None and self._process.poll() is None:
            self._process.kill()
            self._process = None

    def _set_wrong_config_error(self):
        """Set the local error and tip for bad python interpreter configuration
        """

        example = '/usr/bin/python'
        if os.name == 'nt':
            example = r'C:\\Python27\\python.exe'

        self.error = (
            'Anaconda can not spawn a new process with your current '
            'configured python interpreter ({})'.format(
                self.interpreter.raw_interpreter
            )
        )
        self.tip = (
            'Make sure your interpreter is a valid binary and is in '
            'your PATH or use an absolute path to it, '
            'for example: {}'.format(example)
        )
