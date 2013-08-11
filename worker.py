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

from Anaconda.utils import get_settings
from Anaconda.anaconda_client import AnacondaLooper, AsynClient

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.WARNING)


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
        self.loop = AnacondaLooper()
        self.json_server = None
        self.paths = paths
        self.start()

        self.initialized = True

    @property
    def port(self):
        """Get first available port
        """

        if not hasattr(self, '_port') or self.reconnecting:
            s = socket.socket()
            s.bind(('', 0))
            port = s.getsockname()[1]
            s.close()
            self._port = port

        return self._port

    def start(self):
        """Start the client and the loop is there are any clients
        """

        self.start_json_server()
        while not self.server_is_active():
            time.sleep(0.1)

        self.client = AsynClient(self.port)
        if self.loop is None:
            self.loop = AnacondaLooper()

        self.loop.start()

    def start_json_server(self):
        """Starts the JSON server
        """

        if self.server_is_active():
            if self.server_is_healthy():
                return

            self.sanitize_server()

        logger.info('Starting anaconda JSON server...')
        self.build_server()

    def server_is_active(self):
        """Checks if the server is already active
        """

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', self.port))
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

    def server_is_healthy(self):
        """Check if the server process is healthy
        """

        if self.json_server.poll() is None:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(('localhost', self.port))
                s.sendall(bytes('{"method": "check"}', 'utf8'))
                data = sublime.value_decode(s.recv(1024))
                s.close()
            except:
                return False

            return data == b'Ok'
        else:
            logger.error(
                'Something is using the port {} in your system'.format(
                    self.port
                )
            )
            return True

    def sanitize_server(self):
        """Disconnect all the clients and terminate the server process
        """

        asyncore.close_all()
        self.clients = {}
        self.json_server.terminate()
        if self.json_server.poll() is None:
            self.json_server.kill()

    def build_server(self):
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

        args = [python, '-B', script_file,  str(self.port)]
        if self.paths is not None:
            args.extend(['-e', ','.join(self.paths)])

        args.extend([str(os.getpid())])
        self.json_server = subprocess.Popen(args, **kwargs)

    def execute(self, callback, **data):
        """Execute the given method in the remote server
        """

        if not self.client.connected and not self.loop.is_alive():
            if self.json_server.poll() is not None:
                if not self.reconnecting:
                    threading.Thread(target=self.reconnect).start()

        self.client.send_command(callback, **data)

    def reconnect(self):
        """Reconnect
        """

        print('Server crashed... reconnecting...')
        while not self.server_is_active():
            self.reconnecting = True
            self.build_server()
            self.reconnecting = False
            time.sleep(1.0)

        self.client = AsynClient(self.port)
        self.loop = AnacondaLooper()
        self.loop.start()
