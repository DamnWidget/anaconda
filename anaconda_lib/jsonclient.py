# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""Minimalist standard library Asynchronous JSON Client
"""

import sys
import uuid
import logging
import traceback

try:
    import sublime
except ImportError:
    try:
        import ujson as json
    except ImportError:
        import json

from .ioloop import EventHandler

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class AsynClient(EventHandler):
    """Asynchronous JSON connection to anaconda server
    """

    def __init__(self, port):
        EventHandler.__init__(self, ('localhost', port))
        self.callbacks = {}
        self.rbuffer = []

    def ready_to_write(self):
        """I am ready to send some data?
        """

        return True if self.outbuffer else False

    def handle_read(self, data):
        """Called when data is ready to be read
        """

        self.rbuffer.append(data)

    def process_message(self):
        """Called when a full line has been read from the socket
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
                bytes('{}\r\n'.format(sublime.encode_value(data)), 'utf8')
            )
        except NameError:
            self.push(bytes('{}\r\n'.format(json.dumps(data)), 'utf8'))
