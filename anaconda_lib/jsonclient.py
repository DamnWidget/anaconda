# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""Minimalist standard library Asynchronous JSON Client
"""

import sys
import uuid
import logging
import traceback
from ..anaconda_lib import enum


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


class Callback(object):

    @enum.unique
    class CallbackStatus(enum.Enum):
        none = None
        called = 'called'
        success = 'success'
        failure = 'fail'
        timeout = 'timeout'

    def __init__(self, on_success, on_failure=None, on_timeout=None, timeout=0):
        self.uid = uuid.uuid4()
        self.called = self.CallbackStatus.none
        self._status = self.CallbackStatus.none

        # the required callback
        self._on_success = on_success

        # if there is no failure callback use the success one
        self._on_failure = on_failure or on_success

        if callable(on_timeout):
            # allow for custom on_timeout handler
            self._on_timeout = on_timeout

        if timeout:
            sublime.set_timeout(self.on_timeout, timeout * 1000)

    def __call__(self, *args, **kwargs):
        self.test_and_set_called()
        self.set_status_for_data(*args, **kwargs)

        if self.is_success():
            return self._on_success(*args, **kwargs)
        elif self.is_failure():
            return self._on_failure(*args, **kwargs)
        elif self.is_timeout():
            return self._on_timeout(*args, **kwargs)

    @property
    def id(self):
        return self.uid

    @property
    def hexid(self):
        return self.uid.hex

    @property
    def status(self):
        return self._status

    def set_status(self, value):
        """status can only be set once"""
        if self._status == self.CallbackStatus.none:
            if isinstance(value, self.CallbackStatus):
                self._status = value
            else:
                self._status = self.CallbackStatus[value]
        return self._status

    def set_status_for_data(self, *args, **kwargs):
        """
        Set the status based on extracting a code from the callback data.
        Supports two protocols checked in the following order

        1) data = {'callback_status': 'success|failure|timeout' }
        2) data = {'success': True|False}
        """
        data = kwargs.get('data') or args[0] if args else {}

        if 'callback_status' in data:
            self.set_status(data['callback_status'])
        elif 'success' in data:
            if data['success']:
                self.set_status('success')
            else:
                self.set_status('failure')
        else:
            self.set_status('success')

    def is_success(self):
        return self.status is self.CallbackStatus.success

    def is_failure(self):
        return self.status is self.CallbackStatus.failure

    def is_timeout(self):
        return self.status is self.CallbackStatus.timeout

    def test_and_set_called(self):
        """
        Raise an exception if the callback has already fired.
        """
        if self.called is self.CallbackStatus.called:
            raise RuntimeError('Callback can not be used twice')
        self.called = self.CallbackStatus.called

    def on_success(self, *args, **kwargs):
        self.set_status(self.CallbackStatus.success)
        return self(*args, **kwargs)

    def on_failure(self, *args, **kwargs):
        self.set_status(self.CallbackStatus.failure)
        return self(*args, **kwargs)

    def on_timeout(self, *args, **kwargs):
        self.set_status(self.CallbackStatus.timeout)

        if self.is_timeout():
            return self(*args, **kwargs)

    def _on_timeout(self, *args, **kwargs):
        raise RuntimeError('timeout occurred on %s', self.hexid)


class AsynClient(EventHandler):

    """Asynchronous JSON connection to anaconda server
    """

    def __init__(self, port, host='localhost'):
        EventHandler.__init__(self, (host, port))
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

    def add_callback(self, callback):
        if not isinstance(callback, Callback):
            hexid = uuid.uuid4().hex
        else:
            hexid = callback.hexid

        self.callbacks[hexid] = callback
        return hexid

    def pop_callback(self, hexid):
        return self.callbacks.pop(hexid)

    def process_message(self):
        """Called when a full line has been read from the socket
        """

        message = b''.join(self.rbuffer)
        self.rbuffer = []

        try:
            data = sublime.decode_value(message.decode('utf8'))
        except NameError:
            data = json.loads(message.decode('utf8'))

        callback = self.pop_callback(data.pop('uid'))
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
        data['uid'] = self.add_callback(callback)

        try:
            self.push(
                bytes('{}\r\n'.format(sublime.encode_value(data)), 'utf8')
            )
        except NameError:
            self.push(bytes('{}\r\n'.format(json.dumps(data)), 'utf8'))
