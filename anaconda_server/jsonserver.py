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
from functools import partial
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

            if DEBUG_MODE is True:
                print('About push back to ST3: {0}'.format(data))
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

    def run_linter_pylint(self, uid, settings, code, filename):
        """Return lintin errors on the given file
        """

        def merge_pylint_and_pep8(pylint_result, pep8_result):
            """Merge the result from PyLint with the result given by pep8
            """

            self.return_back({
                'success': True,
                'errors': pylint_result['errors'],
                'pep8_errors': pep8_result['errors'],
                'uid': uid
            })

        def lint_pep8(result):
            """Execute the pep8 linter
            """

            callback = partial(merge_pylint_and_pep8, result)
            Lint(callback, uid, linter, settings, code, filename)

        if PYLINT_AVAILABLE:
            PyLint(lint_pep8, uid, PyLinter, filename)
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


class Checker(threading.Thread):
    """Check that the ST3 PID already exists every delta seconds
    """

    def __init__(self, server, delta=5):
        threading.Thread.__init__(self)
        self.server = server
        self.delta = delta
        self.daemon = True
        self.die = False

    def run(self):

        while not self.die:
            if time.time() - self.server.last_call > 1800:
                # is now more than 30 minutes of innactivity
                self.server.logger.info(
                    'detected inactivity for more than 30 minutes... '
                    'shuting down...'
                )
                break

            self._check()
            time.sleep(self.delta)

        self.server.shutdown()

    def _check(self):
        """Check for the ST3 pid
        """

        if os.name == 'posix':
            try:
                os.kill(int(PID), 0)
            except OSError:
                self.server.logger.info(
                    'process {0} does not exists stopping server...'.format(
                        PID
                    )
                )
                self.die = True
        elif os.name == 'nt':
            # win32com is not present in every Python installation on Windows
            # we need something that always work so we are forced here to use
            # the Windows tasklist command and check its output
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output(
                ['tasklist', '/FI', 'PID eq {0}'.format(PID)],
                startupinfo=startupinfo
            )
            pid = PID if not PY3 else bytes(PID, 'utf8')
            if not pid in output:
                self.server.logger.info(
                    'process {0} does not exists stopping server...'.format(
                        PID
                    )
                )
                self.die = True


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
    if len(args) != 2:
        opt_parser.error('you have to pass a port number and PID')

    port = int(args[0])
    PID = args[1]
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
        server = JSONServer(('localhost', port))
        logger.info(
            'Anaconda Server started in port {0} for '
            'PID {1} with cache dir {2}{3}'.format(
                port, PID, jedi.settings.cache_directory,
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

    # start PID checker thread
    if PID != 'DEBUG':
        checker = Checker(server, delta=1)
        checker.start()
    else:
        logger.info('Anaconda Server started in DEBUG mode...')
        print('DEBUG MODE')
        DEBUG_MODE = True

    # start the server
    server.serve_forever()
