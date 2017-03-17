
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import errno
import socket

import sublime

from ..logger import Log
from ..helpers import get_settings
from ..jsonclient import AsynClient
from ..constants import WorkerStatus
from ..decorators import auto_project_switch_ng
from ..helpers import debug_enabled, active_view, is_remote_session

from .process import WorkerProcess
from .interpreter import Interpreter


class Worker(object):
    """Base class for workers
    """

    def __init__(self, interpreter):
        self.status = WorkerStatus.incomplete
        self.interpreter = interpreter
        self.process = WorkerProcess(interpreter).take()
        self.client = None

    @property
    def unix_socket(self):
        """Determine if we use an Unix Socket
        """

        for_local = self.interpreter.for_local
        return for_local and sublime.platform() == 'linux'

    def start(self):
        """Start the worker
        """

        if not debug_enabled(active_view()):
            if self.process is None:
                Log.fatal('Worker process is None!!')
                return

            if not self.process.start():
                msg = (
                    '{} process can not start a new anaconda JsonServer '
                    'in the operating system because:\n\n{}\n\n{}'.format(
                        self.process, self.process.error, self.process.tip
                    )
                )
                Log.error(msg)
                if self.status != WorkerStatus.faulty:
                    if not get_settings(
                            active_view(), 'swallow_startup_errors', False):
                        sublime.error_message(msg)
                    self.status = WorkerStatus.faulty
                return

        if not self.check():
            msg = (
                '{} initial check failed because:\n\n{}\n\n{}'.format(
                    self, self.error, self.tip
                )
            )

            Log.error(msg)
            if self.status != WorkerStatus.faulty:
                if not get_settings(
                        active_view(), 'swallow_startup_errors', False):
                    sublime.error_message(msg)
                self.status = WorkerStatus.faulty
            return

        host, port = self.interpreter.host, self.interpreter.port
        if self.unix_socket:
            port = 0
        self.client = AsynClient(int(port), host=host)
        self.status = WorkerStatus.healthy
        if hasattr(self, 'reconnecting') and self.reconnecting:
            self.reconnecting = False

    def stop(self):
        """Stop the worker
        """
        pass

    def check(self):
        """This method must be re-implemented in base classes
        """

        raise RuntimeError('this method must be re-implemented')

    def renew_interpreter(self, raw_interpreter):
        """Renew the interpreter object (as it has changed in the configuration)
        """

        self.interpreter = Interpreter(raw_interpreter)
        self.process.interpreter = self.interpreter

    @auto_project_switch_ng
    def _execute(self, callback, **data):
        """Execute the given method in the remote server
        """

        self.client.send_command(callback, **data)

    def _get_service_socket(self, timeout=0.05):
        """Helper function that returns a socket to the JsonServer process
        """

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((self.interpreter.host, int(self.interpreter.port)))
        return s

    def _get_service_unix_socket(self, timeout=0.05):
        """Helper function that returns a unix socket to JsonServer process
        """

        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(self.interpreter.host)
        return s

    def _append_context_data(self, data):
        """Append contextual data depending on the worker type
        """

        view = active_view()
        if is_remote_session(view):
            directory_map = self.interpreter.pathmap
            if directory_map is None:
                return

            for local_dir, remote_dir in directory_map.items():
                # the directory os mapped on the remote machine
                data['filename'] = view.file_name().replace(
                    local_dir, remote_dir
                )
                break

    def _status(self, timeout=2):
        """Check the socket status, return True if it is operable
        """

        service_func = {
            True: self._get_service_unix_socket,
            False: self._get_service_socket
        }

        try:
            s = service_func[self.unix_socket](timeout)
            s.close()
            self.error = False
        except socket.timeout:
            self.error = 'connection to {}:{} timed out after {}s'.format(
                self.interpreter.host, self.interpreter.port, timeout
            )
            return False
        except socket.error as error:
            if error.errno == errno.ECONNREFUSED:
                if self.unix_socket:
                    self.error = 'can not connect to {}'.format(
                        self.interpreter.host
                    )
                else:
                    self.error = 'can not connect to {} in port {}'.format(
                        self.interpreter.host, self.interpreter.port
                    )
            else:
                self.error = 'unexpected exception: {}'.format(error)
            return False

        return True
