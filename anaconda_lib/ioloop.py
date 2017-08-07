# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Minimalist asynchronous network library just to fit Anaconda's needs and
replace the horrible asyncore/asynchat

Example of usage:

import ioloop

class TestClient(ioloop.EventHandler):
    '''Client for test
    '''

    def __init__(self, host, port):
        ioloop.EventHandler.__init__(self, (host, port))
        self.message = []

    def ready_to_write(self):
        return True if self.outbuffer else False

    def handle_read(self, data):
        self.message.append(data)

    def process_message(self):
        print(b''.join(self.message))
        self.message = []

"""

import os
import sys
import time
import errno
import socket
import select
import logging
import traceback
import threading

from ._typing import List, Tuple, Any  # noqa

NOT_TERMINATE = True


class IOHandlers(object):
    """Class that register and unregister IOHandler
    """

    _shared_state = {}  # type: Dict[Any, Any]

    def __init__(self) -> None:
        self.__dict__ = IOHandlers._shared_state
        if hasattr(self, 'instanced') and self.instanced is True:
            return

        self._handler_pool = {}  # type: Dict[int, EventHandler]
        self._lock = threading.Lock()
        self.instanced = True  # type: bool

    def ready_to_read(self) -> List['EventHandler']:
        """Return back all the handlers that are ready to read
        """

        return [h for h in self._handler_pool.values() if h.ready_to_read()]

    def ready_to_write(self):
        """Return back all the handlers that are ready to write
        """

        return [h for h in self._handler_pool.values() if h.ready_to_write()]

    def register(self, handler):
        """Register a new handler
        """

        logging.info(
            'Registering handler with address {}'.format(handler.address))

        with self._lock:
            if handler.fileno() not in self._handler_pool:
                self._handler_pool.update({handler.fileno(): handler})

    def unregister(self, handler):
        """Unregister the given handler
        """

        with self._lock:
            if handler.fileno() in self._handler_pool:
                self._handler_pool.pop(handler.fileno())


class EventHandler(object):
    """Event handler class
    """

    def __init__(self, address: Tuple[str, int], sock: socket.socket=None) -> None:  # noqa
        self._write_lock = threading.RLock()
        self._read_lock = threading.RLock()
        self.address = address
        self.outbuffer = b''
        self.inbuffer = b''
        self.sock = sock
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock.connect(address)
        self.connected = True
        self.sock.setblocking(False)
        IOHandlers().register(self)

    def __del__(self) -> None:
        if self in IOHandlers()._handler_pool.values():
            IOHandlers().unregister(self)

    def fileno(self) -> int:
        """Return the associated file descriptor
        """

        return self.sock.fileno()

    def send(self) -> int:
        """Send outgoing data
        """

        with self._write_lock:
            while len(self.outbuffer) > 0:
                try:
                    sent = self.sock.send(self.outbuffer)
                    self.outbuffer = self.outbuffer[sent:]
                except socket.error as error:
                    if error.args[0] == errno.EAGAIN:
                        time.sleep(0.1)
                    elif error.args[0] in (
                        errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN,
                        errno.ECONNABORTED, errno.EPIPE
                    ):
                        self.close()
                        return 0
                    elif os.name == 'posix':
                        # Windows doesn't seems to have EBADFD
                        if sys.platform == 'darwin':
                            # OS X uses EBADF as EBADFD. why? no idea asks Tim
                            if error.args[0] == errno.EBADF:
                                self.close()
                                return 0
                        else:
                            if error.args[0] == errno.EBADFD:
                                self.close()
                                return 0
                        raise
                    else:
                        raise

    def recv(self) -> None:
        """Receive some data
        """

        try:
            data = self.sock.recv(4096)
        except socket.error as error:
            if error.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                return None
            elif error.args[0] == errno.ECONNRESET:
                self.close()
                return None
            else:
                raise

        if not data:
            self.close()
            return None

        self.inbuffer += data

        while self.inbuffer:
            match = b'\r\n'
            index = self.inbuffer.find(match)
            if index != -1:
                if index > 0:
                    self.handle_read(self.inbuffer[:index])

                self.inbuffer = self.inbuffer[index+len(match):]
                self.process_message()
            else:
                index = len(match) - 1
                while index and not self.inbuffer.endswith(match[:index]):
                    index -= 1

                if index:
                    if index != len(self.inbuffer):
                        self.handle_read(self.inbuffer[:-index])
                        self.inbuffer = self.inbuffer[-index:]
                    break
                else:
                    self.handle_read(self.inbuffer)
                    self.inbuffer = b''

    def push(self, data: bytes) -> None:
        """Push some bytes into the write buffer
        """

        self.outbuffer += data

    def handle_read(self, data: bytes) -> None:
        """Handle data readign from select
        """

        raise RuntimeError('You have to implement this method')

    def process_message(self) -> None:
        """Process the full message
        """

        raise RuntimeError('You have to implement this method')

    def ready_to_read(self) -> bool:
        """This handler is ready to read
        """

        return True

    def ready_to_write(self) -> bool:
        """This handler is ready to write
        """

        return True

    def close(self) -> None:
        """Close the socket and unregister the handler
        """

        if self in IOHandlers()._handler_pool.values():
            IOHandlers().unregister(self)

        self.sock.close()
        self.connected = False


def poll() -> None:
    """Poll the select
    """

    recv = send = []  # type: List[bytes]
    try:
        if os.name != 'posix':
            if IOHandlers()._handler_pool:
                recv, send, _ = select.select(
                    IOHandlers().ready_to_read(),
                    IOHandlers().ready_to_write(),
                    [], 0
                )
        else:
            recv, send, _ = select.select(
                IOHandlers().ready_to_read(), IOHandlers().ready_to_write(),
                [], 0
            )
    except select.error:
        err = sys.exc_info()[1]
        if err.args[0] == errno.EINTR:
            return
        raise

    for handler in recv:
        if handler is None or handler.ready_to_read() is not True:
            continue
        handler.recv()

    for handler in send:
        if handler is None or handler.ready_to_write() is not True:
            continue
        handler.send()


def loop() -> None:
    """Main event loop
    """

    def restart_poll(error: Exception) -> None:
        logging.error(
            'Unhandled exception in poll, restarting the poll request')
        logging.error(error)
        for traceback_line in traceback.format_exc().splitlines():
            logging.error(traceback_line)

        with IOHandlers()._lock:
            for handler in IOHandlers()._handler_pool.values():
                handler.close()
            IOHandlers()._handler_pool = {}

    def inner_loop() -> None:

        while NOT_TERMINATE:
            try:
                poll()
                time.sleep(0.01)
            except OSError as error:
                if os.name != 'posix' and error.errno == os.errno.WSAENOTSOCK:
                    msg = (
                        'Unfortunately, the Windows socket is in inconsistent'
                        ' state, restart your sublime text 3. If the problem '
                        'persist, fill an issue report on:'
                        '   https://github.com/DamnWidget/anaconda/issues'
                    )
                    logging.error(msg)
                    import sublime
                    sublime.error_message(msg)
                    terminate()
                else:
                    restart_poll(error)
            except Exception as error:
                restart_poll(error)

        # cleanup
        for handler in IOHandlers()._handler_pool.values():
            handler.close()

    threading.Thread(target=inner_loop).start()


def terminate() -> None:
    """Terminate the loop
    """

    global NOT_TERMINATE
    NOT_TERMINATE = False


def restart() -> None:
    """Restart the loop
    """

    global NOT_TERMINATE
    if NOT_TERMINATE is True:
        NOT_TERMINATE = False

    terminate()
    NOT_TERMINATE = True
    loop()
