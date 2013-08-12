# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""Minimalist standard library Asynchronous JSON Client
"""

import sys
import uuid
import socket
import logging
import asyncore
import asynchat
import threading
import traceback

try:
    import sublime
except ImportError:
    try:
        import ujson as json
    except ImportError:
        import json

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class AsynClient(asynchat.async_chat):
    """Asynchronous JSON connection to anaconda server
    """

    def __init__(self, port, loop_map):
        self.port = port
        self.callbacks = {}
        self.rbuffer = []
        asynchat.async_chat.__init__(self, map=loop_map)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.debug('Connecting to localhost on port {}'.format(port))
        self.connect(('localhost', port))

    def handle_connect(self):
        """Called on connection stablished
        """

        logger.debug('The connection has been stablished')
        self.set_terminator(b"\r\n")

    def collect_incoming_data(self, data):
        """Called when data is ready to be read
        """

        self.rbuffer.append(data)

    def found_terminator(self):
        """Called when a terminator is found
        """

        message = b''.join(self.rbuffer)
        self.rbuffer = []

        try:
            data = sublime.decode_value(message.decode('utf8'))
        except NameError:
            data = json.loads(message.decode('utf8'))

        callback = self.callbacks.pop(data.pop('uid'))
        if callback is None:
            logger.error(
                'Received {} from the JSONServer but there is not callback '
                'to handle it. Aborting....'.format(message)
            )

        try:
            callback(data)
        except Exception as error:
            logging.error(error)
            for traceback_line in traceback.format_exc().splitlines():
                logging.error(traceback_line)

    def send_command(self, callback, **data):
        """Send the given command that should be handled bu the given callback
        """

        uid = uuid.uuid4()
        self.callbacks[uid.hex] = callback
        data['uid'] = uid.hex

        try:
            self.push(
                bytes('{};aend;'.format(sublime.encode_value(data)), 'utf8')
            )
        except NameError:
            self.push(bytes('{};aend;'.format(json.dumps(data)), 'utf8'))
