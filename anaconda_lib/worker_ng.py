
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import socket
import logging

import sublime

from .jsonclient import AsynClient
from .constants import WorkerStatus
from .decorators import auto_project_switch
from .helpers import get_settings, active_view, is_remote_session

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.WARNING)


class Worker(object):
    """Base class for worker generic interface
    """

    def __init__(self, checker=None, processer=None):

        self._header = 'In {}.{}: '.format(
            self.__module__, self.__class__.__name__)
        self.status = WorkerStatus.incomplete
        self.client = None
        self.checker = checker
        self.processer = processer

    @property
    def port(self):
        """Return the right port for the given Worker checker
        """

        return self.checker.port

    @property
    def hostaddr(self):
        """Return the right port for the given Worker checker
        """

        return self.checker.hostaddr

    def start(self):
        """Start the worker and it's services
        """

        if not get_settings(active_view(), 'jsonserver_debug', False):
            if not self.processer.start(self):
                msg = (
                    '{} processer could not start a new anaconda '
                    'JsonServer with reason:\n\t{}\n\n{}'
                ).format(
                    self._header,
                    self.processer.last_error.get('error', 'none'),
                    self.processer.last_error.get('recommendation', '')
                )
                logger.error(msg)
                if self.status != WorkerStatus.faulty:
                    sublime.error_message(msg)
                    self.status = WorkerStatus.faulty
                return

        if not self.checker.check(self):
            msg = (
                '{} initial check failed with reason:\n\t{}\n\n{}'
            ).format(
                self._header,
                self.checker.last_error.get('error', 'none'),
                self.checker.last_error.get(
                    'recommendation', 'check jsonserver_debug is not active')
            )
            logger.error(msg)
            if self.status != WorkerStatus.faulty:
                sublime.error_message(msg)
                self.status = WorkerStatus.faulty
            return

        self.client = AsynClient(self.port, host=self.hostaddr)
        self.status = WorkerStatus.healthy

    def stop(self):
        """Stop base implementation does nothing
        """

        pass

    @auto_project_switch
    def _execute(self, callback, **data):
        """Execute the given method in the remote server
        """

        self.client.send_command(callback, **data)

    def __repr__(self):
        """String representation of this worker
        """

        return 'Worker({}) {} ({})\n\tClient: {}\n'.format(
            self.__class__.__name__, id(self), self.status, self.client
        )

    def _get_service_socket(self, timeout=0.05):
        """Helper function that return a socket to the local worker
        """

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((self.hostaddr, self.port))
        return s

    def _append_context_data(self, data):
        """Append contextual data depending on the worker type
        """

        view = active_view()
        if is_remote_session(view):
            directory_map = self.rc.get('pathmap', {})
            for local_dir, remote_dir in directory_map.items():
                if local_dir in os.path.realpath(view.file_name()):
                    # the directory is mapped on the rmeote machine
                    data['filename'] = view.file_name().replace(
                        local_dir, remote_dir
                    )
                    break
