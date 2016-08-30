# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import time
import socket
import logging
import asyncore
import asynchat
import traceback
from logging import handlers
from optparse import OptionParser

# we use ujson if it's available on the target intrepreter
try:
    import ujson as json
except ImportError:
    import json

sys.path.insert(0, os.path.join(
    os.path.split(os.path.split(__file__)[0])[0], 'anaconda_lib'))

from jedi import settings as jedi_settings

from lib.path import log_directory
from lib.contexts import json_decode
from handlers import ANACONDA_HANDLERS
from lib.anaconda_handler import AnacondaHandler

DEBUG_MODE = False
logger = logging.getLogger('')
PY3 = True if sys.version_info >= (3,) else False


class JSONHandler(asynchat.async_chat):
    """Handles JSON messages from a client
    """

    def __init__(self, sock, server):
        self.server = server
        self.rbuffer = []
        asynchat.async_chat.__init__(self, sock)
        self.set_terminator(b"\r\n" if PY3 else "\r\n")

    def return_back(self, data):
        """Send data back to the client
        """

        if data is not None:
            data = '{0}\r\n'.format(json.dumps(data))
            data = bytes(data, 'utf8') if PY3 else data

            if DEBUG_MODE is True:
                print('About push back to ST3: {0}'.format(data))
                logging.info('About push back to ST3: {0}'.format(data))
            self.push(data)

    def collect_incoming_data(self, data):
        """Called when data is ready to be read
        """

        self.rbuffer.append(data)

    def found_terminator(self):
        """Called when the terminator is found in the buffer
        """

        message = b''.join(self.rbuffer) if PY3 else ''.join(self.rbuffer)
        self.rbuffer = []

        with json_decode(message) as data:
            if not data:
                logging.info('No data received in the handler')
                return

            if data['method'] == 'check':
                self.return_back(message='Ok', uid=data['uid'])
                return

            self.server.last_call = time.time()

        if type(data) is dict:
            logging.info(
                'client requests: {0}'.format(data['method'])
            )

            method = data.pop('method')
            uid = data.pop('uid')
            vid = data.pop('vid', None)
            handler_type = data.pop('handler')
            self.handle_command(handler_type, method, uid, vid, data)
        else:
            logging.error(
                'client sent something that I don\'t understand: {0}'.format(
                    data
                )
            )

    def handle_command(self, handler_type, method, uid, vid, data):
        """Call the right commands handler
        """

        # lazy initialization of anaconda plugins
        if not AnacondaHandler._registry.initialized:
            AnacondaHandler._registry.initialize()

        handler = ANACONDA_HANDLERS.get(
            handler_type, AnacondaHandler.get_handler(handler_type))
        handler(method, data, uid, vid, self.return_back, DEBUG_MODE).run()


class JSONServer(asyncore.dispatcher):
    """Asynchronous standard library TCP JSON server
    """

    allow_reuse_address = False
    request_queue_size = 5
    address_familty = socket.AF_INET
    socket_type = socket.SOCK_STREAM

    def __init__(self, address, handler=JSONHandler):
        self.address = address
        self.handler = handler

        asyncore.dispatcher.__init__(self)
        self.create_socket(self.address_familty, self.socket_type)
        self.last_call = time.time()

        self.bind(self.address)
        logging.debug('bind: address=%s' % (address,))
        self.listen(self.request_queue_size)
        logging.debug('listen: backlog=%d' % (self.request_queue_size,))

    @property
    def fileno(self):
        return self.socket.fileno()

    def serve_forever(self):
        asyncore.loop()

    def shutdown(self):
        self.handle_close()

    def handle_accept(self):
        """Called when we accept and incomming connection
        """
        sock, addr = self.accept()
        self.logger.info('Incomming connection from {0}'.format(repr(addr)))
        self.handler(sock, self)

    def handle_close(self):
        """Called when close
        """

        logging.info('Closing the socket, server will be shutdown now...')
        self.close()


def get_logger(path):
    """Build file logger
    """

    if not os.path.exists(path):
        os.makedirs(path)

    log = logging.getLogger('')
    log.setLevel(logging.DEBUG)
    hdlr = handlers.RotatingFileHandler(
        filename=os.path.join(path, 'anaconda_jsonserver.log'),
        maxBytes=10000000,
        backupCount=5,
        encoding='utf-8'
    )
    formatter = logging.Formatter('%(asctime)s: %(levelname)-8s: %(message)s')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    return log


def log_traceback():
    """Just log the traceback
    """

    logging.error(get_log_traceback())


def get_log_traceback():
    """Get the traceback log msg
    """

    error = []
    for traceback_line in traceback.format_exc().splitlines():
        error.append(traceback_line)

    return '\n'.join(error)

if __name__ == "__main__":
    opt_parser = OptionParser(usage=(
        'usage: %prog -p <project> -e <extra_paths> port'
    ))

    opt_parser.add_option(
        '-p', '--project', action='store', dest='project', help='project name'
    )

    opt_parser.add_option(
        '-e', '--extra_paths', action='store', dest='extra_paths',
        help='extra paths (separed by comma) that should be added to sys.paths'
    )

    options, args = opt_parser.parse_args()
    if len(args) != 1:
        opt_parser.error('you have to pass a port number')

    port = int(args[0])
    if options.project is not None:
        jedi_settings.cache_directory = os.path.join(
            jedi_settings.cache_directory, options.project
        )
        log_directory = os.path.join(log_directory, options.project)

    if not os.path.exists(jedi_settings.cache_directory):
        os.makedirs(jedi_settings.cache_directory)

    if options.extra_paths is not None:
        for path in options.extra_paths.split(','):
            if path not in sys.path:
                sys.path.insert(0, path)

    logger = get_logger(log_directory)

    try:
        server = JSONServer(('0.0.0.0', port))
        logger.info(
            'Anaconda Server started in port {0} with cache dir {1}{2}'.format(
                port, jedi_settings.cache_directory,
                ' and extra paths {0}'.format(
                    options.extra_paths
                ) if options.extra_paths is not None else ''
            )
        )
    except Exception as error:
        log_traceback()
        logger.error(error)
        sys.exit(-1)

    server.logger = logger

    # start the server
    server.serve_forever()
