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
import threading
import traceback
import subprocess
from logging import handlers
from optparse import OptionParser

# we use ujson if it's available on the target intrepreter
try:
    import ujson as json
except ImportError:
    import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../anaconda_lib'))

import jedi
from linting import linter
from contexts import json_decode
from jedi import refactoring as jedi_refactor
from commands import (
    Doc, Lint, Goto, Rename, PyLint, FindUsages, AutoComplete,
    CompleteParameters
)

try:
    from linting.anaconda_pylint import PyLinter
    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False


DEBUG_MODE = False
logger = logging.getLogger('')
PY3 = True if sys.version_info >= (3,) else False


class JSONHandler(asynchat.async_chat):
    """Hadnles JSON messages from a client
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

        with json_decode(message) as self.data:
            if not self.data:
                logging.info('No data received in the handler')
                return

            if self.data['method'] == 'check':
                self.return_back('Ok')
                return

            self.server.last_call = time.time()

        if type(self.data) is dict:
            logging.info(
                'client requests: {0}'.format(self.data['method'])
            )

            method = self.data.pop('method')
            uid = self.data.pop('uid')
            if 'lint' in method:
                self.handle_lint_command(method, uid)
            elif 'refactor' in method:
                self.handle_refactor_command(method, uid)
            else:
                self.handle_jedi_command(method, uid)
        else:
            logging.error(
                'client sent somethinf that I don\'t understand: {0}'.format(
                    self.data
                )
            )

    def handle_lint_command(self, method, uid):
        """Handle lint command
        """

        getattr(self, method)(uid, **self.data)

    def handle_refactor_command(self, method, uid):
        """Handle refactor command
        """

        self.script = self.jedi_script(
            self.data.pop('source'),
            self.data.pop('line'),
            self.data.pop('offset'),
            filename=self.data.pop('filename'),
            encoding='utf8'
        )
        getattr(self, method.split('_')[1])(uid, **self.data)

    def handle_jedi_command(self, method, uid):
        """Handle jedi related commands
        """

        kwargs = {}
        if 'settings' in self.data:
            kwargs.update({'settings': self.data.pop('settings')})

        self.script = self.jedi_script(**self.data)
        getattr(self, method)(uid, **kwargs)

    def jedi_script(self, source, line, offset, filename='', encoding='utf8'):
        if DEBUG_MODE is True:
            logging.debug(
                'jedi_script called with the following parameters: '
                'source: {0}\nline: {1} offset: {2}, filename: {3}'.format(
                    source, line, offset, filename
                )
            )
        return jedi.Script(
            source, int(line), int(offset), filename, encoding
        )

    def run_linter(self, uid, settings, code, filename):
        """Return lintin errors on the given code
        """

        Lint(self.return_back, uid, linter, settings, code, filename)

    def run_linter_pylint(self, uid, filename):
        """Return lintin errors on the given file
        """

        if PYLINT_AVAILABLE:
            PyLint(self.return_back, uid, PyLinter, filename)
        else:
            success = False
            errors = 'Your configured python interpreter can\'t import pylint'

        self.return_back({
            'success': success,
            'errors': errors,
            'uid': uid
        })

    def rename(self, uid, directories, new_word):
        """Rename the object under the cursor by the given word
        """

        Rename(
            self.return_back, uid, self.script,
            directories, new_word, jedi_refactor
        )

    def autocomplete(self, uid):
        """Call autocomplete
        """
        AutoComplete(self.return_back, uid, self.script)

    def parameters(self, uid, settings):
        """Call complete parameters
        """
        CompleteParameters(self.return_back, uid, self.script, settings)

    def usages(self, uid):
        """Call Find Usages
        """
        FindUsages(self.return_back, uid, self.script)

    def goto(self, uid):
        """Call goto
        """
        Goto(self.return_back, uid, self.script)

    def doc(self, uid):
        """Call doc
        """
        Doc(self.return_back, uid, self.script)


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
        jedi.settings.cache_directory = os.path.join(
            jedi.settings.cache_directory, options.project
        )

    if not os.path.exists(jedi.settings.cache_directory):
        os.makedirs(jedi.settings.cache_directory)

    if options.extra_paths is not None:
        for path in options.extra_paths.split(','):
            if path not in sys.path:
                sys.path.insert(0, path)

    logger = get_logger(jedi.settings.cache_directory)

    try:
        server = JSONServer(('0.0.0.0', port))
        logger.info(
            'Anaconda Server started in port {0} with cache dir {1}{2}'.format(
                port, jedi.settings.cache_directory,
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
