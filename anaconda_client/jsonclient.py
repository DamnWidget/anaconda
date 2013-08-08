# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sys
import errno
import socket
import logging

import sublime


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class Client:
    """JSON Connection to anaconda server
    """

    def __init__(self, host, port=None):

        self.host = host
        self.port = port
        self.sock = None
        self.rfile = None
        self.wfile = None
        self.rbufsize = -1
        self.wbufsize = 0

    def connect(self):
        """Connect to the specified host and port in constructor time
        """

        self.sock = socket.create_connection((self.host, self.port))

        self.rfile = self.sock.makefile('r')
        self.wfile = self.sock.makefile('w')

    def close(self):
        """Close the connection to the anaconda server
        """

        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, data):
        """
        Send data to the anaconda server in JSON formated string with
        new line ending
        """

        if self.sock is None:
            self.connect()

        try:
            self.wfile.write('{}\r\n'.format(data))
            self.wfile.flush()
        except socket.error as error:
            if error.errno == errno.EPIPE:
                logger.error('Connection unexpectedly closed with EPIPE')
                self._clean_socket()
                return {'success': False, 'message': 'EPIPE'}

    def request(self, method, **kwargs):
        """Send a request to the server
        """

        kwargs['method'] = method
        self.send(sublime.encode_value(kwargs))

        return self.getresponse()

    def getresponse(self):
        """Get the response from the server
        """

        try:
            line = self.rfile.readline()
        except socket.error as e:
            logger.error('Connection unexpectedly closed: ' + str(e))
            line = '{"success": false, "message": "{0}"}'.format(str(e))
            self._clean_socket()

        if not line:
            logger.error('Connection unexpectedly closed')
            line = (
                '{"success": false, "message": '
                '"Connection unexpectedly closed"}'
            )
            self._clean_socket()

        return sublime.decode_value(line)

    def _clean_socket(self):
        """Close the socket and clean the related resources
        """

        self.rfile.close()
        self.wfile.close()
        self.file = None
        self.close()
