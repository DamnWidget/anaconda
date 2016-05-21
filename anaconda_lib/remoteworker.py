
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import errno
import socket
import logging

from urllib.parse import parse_qs

from .worker_ng import Worker
from .constants import WorkerStatus
from .helpers import active_view, get_settings

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.WARNING)


class RemoteWorker(Worker):
    """This class implements a generic remote worker
    """

    def __init__(self, data, checker=None, processer=None):

        self.rc = {}
        self.reconnecting = False
        super(RemoteWorker, self).__init__(
            RemoteChecker() if checker is None else checker,
            StubProcesser() if processer is None else processer
        )
        self._parse_uri_data(data)

    def _parse_uri_data(self, data):
        """Parses the URI for this Remote Worker
        """

        netloc = data['netloc']
        query = data['query']

        split_netloc = netloc.split(':')
        if len(split_netloc) != 2:
            self.rc['host'], self.rc['port'] = split_netloc
        else:
            try:
                self.rc['port'] = int(netloc)
                self.rc['host'] = 'localhost'
            except ValueError:
                self.rc['host'] = netloc
                self.rc['port'] = 9999

        options = {}
        if query:
            options = parse_qs(query)

        pathmap = {}
        for map_data in options.get('pathmap', []):
            split_data = map_data.split(',')
            if len(split_data) != 2:
                logger.warning('pathmap corruption? -> {}'.format(map_data))
                continue

            local_path = os.path.expanduser(os.path.expandvars(split_data[0]))
            remote_path = os.path.expanduser(os.path.expandvars(split_data[1]))
            pathmap[local_path] = remote_path

        self.rc['pathmap'] = pathmap


class StubProcesser(object):
    """Just a stub dummy class to don't fail on generic Worker start
    """

    def __init__(self):
        self._process = None

    def start(self, worker):
        """just returns True and does nothing
        """

        return True


class RemoteChecker(object):
    """Implement generic checks for remote JsonServer support
    """

    def __init__(self):
        self.rc = {}
        self.last_error = {}
        self._remote_addr = None

    @property
    def port(self):
        """Return the port extracting it from the python_interpreter
        """

        # check for debug options
        if get_settings(active_view(), 'jsonserver_debug', False):
            return get_settings(active_view(), 'jsonserver_debug_port', 9999)

        if self._remote_addr is not None:
            return self._remote_addr[1]

        self._extract_addr()
        return self.port

    @property
    def hostaddr(self):
        """Return the addr extracting it from the python_interpreter
        """

        if self._remote_addr is not None:
            return self._remote_addr[0]

        self._extract_addr()
        return self.hostaddr

    def check(self, worker):
        """Perform required checks to conclude if it's safe to operate
        """

        # if last_error is not empty just return False
        if not not self.last_error:
            return False

        return self._status(worker)

    def _compile_path_maps(self):
        """Compile the connection pathmaps if any and return it back
        """

        pathmap = {}
        for map_data in self.rc.get('pathmap', []):
            split_data = map_data.split(',')
            if len(split_data) != 2:
                logger.warning('pathmap corruption? -> {}'.format(map_data))
                continue

            local_path = os.path.expanduser(os.path.expanvars(split_data[0]))
            remote_path = os.path.expanduser(os.path.expandvars(split_data[1]))
            pathmap[local_path] = remote_path

        return pathmap

    def _status(self, worker, timeout=2):
        """Check the socket status and return True if is operable
        """

        recommendation = (
            'check that your internet is working, the remote host is '
            'available from your network and the jsonserver.py is '
            'running in the remote host on port {}'.format(self.port)
        )

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((worker.hostaddr, worker.port))
            s.close()
            self.last_error = {}
        except socket.timeout:
            self.last_error = {
                'error': 'conn to {} in port {} timed out after 2s'.format(
                    self.hostaddr, self.port
                ),
                'recommendation': recommendation
            }
            self.status = WorkerStatus.faulty
            return False
        except socket.error as error:
            if error.errno is errno.ECONNREFUSED:
                self.last_error = {
                    'error': 'can not connect to {} in port {}'.format(
                        self.hostaddr, self.port
                    ),
                    'recommendation': recommendation
                }
            else:
                self.last_error = {
                    'error': 'Unexpected exception: {}'.format(error),
                    'recommendation': recommendation
                }
            self.status = WorkerStatus.faulty
            return False

        return True

    def _extract_addr(self):
        """Extract the addr as a tuple (hostaddr, port) from python_interpreter
        """

        host, port = None, None
        interpreter = get_settings(active_view(), 'python_interpreter')
        try:
            host, port = interpreter[6:].split(':')
        except Exception as error:
            self.last_error = {
                'error': (
                    'invalid settings for remote server {}: {}'.format(
                        interpreter, error)
                ),
                'recommendation': 'use a valid hostaddr:port format'
            }

        self._remote_addr = (host, int(port))
