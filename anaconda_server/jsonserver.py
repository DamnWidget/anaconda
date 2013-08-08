# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import time
import errno
import logging
import threading
import traceback
import subprocess
from logging import handlers
from optparse import OptionParser

if sys.version_info[0] == 2:
    import SocketServer as socketserver
else:
    import socketserver

# we use ujson if it's available on the target intrepreter
try:
    import ujson as json
except ImportError:
    import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

import jedi
from linting import linter
from decorators import timeit
from contexts import json_decode

DEBUG_MODE = False


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

logger = get_logger(jedi.settings.cache_directory)


class ThreadedJSONServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threading JSON Server
    """

    locker = threading.RLock()
    last_call = time.time()


class JSONHandler(socketserver.StreamRequestHandler):
    """Handler Class for the Anaconda JSON server
    """

    def handle(self):
        """This function handles requests from anaconda plugin
        """

        with json_decode(self.rfile.readline().strip()) as self.data:
            with self.server.locker:
                self.server.last_call = time.time()

            logging.info(
                '{0} requests: {1}'.format(
                    self.client_address[0], self.data['method']
                )
            )

        if type(self.data) is dict:
            try:
                method = self.data.pop('method')
                if 'lint' in method:
                    self.handle_lint_command(method)
                else:
                    self.handle_jedi_command(method)
            except IOError as error:
                if error.errno == errno.EPIPE:
                    logging.error('Error [32]Broken PIPE Killing myself... ')
                    self.shutdown()
                    sys.exit()
            except Exception as error:
                logging.info('Exception: {0}'.format(error))
                log_traceback()
        else:
            logging.error(
                '{0} sent something that I dont undertand: {1}'.format(
                    self.client_address[0], self.data
                )
            )

    def handle_lint_command(self, method):
        """Handle lint related commands
        """

        getattr(self, method)(**self.data)

    def handle_jedi_command(self, method):
        """Handle jedi related commands
        """

        self.script = self.jedi_script(**self.data)
        getattr(self, method)()

    def jedi_script(self, source, line, offset, filename='', encoding='utf-8'):
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

    def run_linter(self, settings, code, filename):
        """Return linting errors on the given code
        """

        result = {
            'success': True, 'errors': linter.Linter().run_linter(
                settings, code, filename
            )
        }

        self.wfile.write('{}\r\n'.format(json.dumps(result)))

    def autocomplete(self):
        """Return Jedi completions
        """

        try:
            data = self._parameters_for_complete()

            completions = self.script.completions()
            if DEBUG_MODE is True:
                logging.info(completions)
            data.extend([
                ('{0}\t{1}'.format(comp.name, comp.type), comp.name)
                for comp in completions
            ])
            result = {'success': True, 'completions': data}
        except Exception as error:
            logging.error('The underlying Jedi library as raised an exception')
            logging.error(error)
            log_traceback()
            result = {
                'success': False,
                'error': str(error),
                'tb': get_log_traceback()
            }

        self.wfile.write('{}\r\n'.format(json.dumps(result)))

    def goto(self):
        """Goto a Python definition
        """

        try:
            definitions = self.script.goto_assignments()
            if all(d.type == 'import' for d in definitions):
                definitions = self.script.goto_definitions()
        except jedi.api.NotFoundError:
            data = None
            success = False
        else:
            data = [(i.module_path, i.line, i.column + 1)
                    for i in definitions if not i.in_builtin_module()]
            success = True

        self.wfile.write('{}\r\n'.format(json.dumps({
            'success': success, 'goto': data
        })))

    def usages(self):
        """Find usages
        """

        try:
            usages = self.script.usages()
            success = True
        except jedi.api.NotFoundError:
            usages = None
            success = False

        self.wfile.write('{}\r\n'.format(json.dumps({
            'success': success, 'usages': [
                (i.module_path, i.line, i.column)
                for i in usages if not i.in_builtin_module()
            ] if usages is not None else []
        })))

    def doc(self):
        """Find documentation
        """

        try:
            definitions = self.script.goto_definitions()
        except jedi.NotFoundError:
            definitions = []
        except Exception:
            definitions = []
            logging.error('Exception, this shouldn\'t happen')
            log_traceback()

        if not definitions:
            success = False
            docs = []
        else:
            success = True
            docs = [
                'Docstring for {0}\n{1}\n{2}'.format(
                    d.full_name, '=' * 40, d.doc
                ) if d.doc else 'No docstring for {0}'.format(d)
                for d in definitions
            ]

        self.wfile.write('{}\r\n'.format(json.dumps({
            'success': success, 'doc': ('\n' + '-' * 79 + '\n').join(docs)
        })))

    def _parameters_for_complete(self):
        """Get function / class constructor paremeters completions list
        """

        completions = []
        try:
            in_call = self.script.call_signatures()[0]
        except IndexError:
            in_call = None

        parameters = self._get_function_parameters(in_call)

        for parameter in parameters:
            try:
                name, value = parameter
            except ValueError:
                name = parameter[0]
                value = None

            if value is None:
                completions.append((name, '${1:%s}' % name))
            else:
                completions.append(
                    (name + '\t' + value, '%s=${1:%s}' % (name, value))
                )

        return completions

    def _get_function_parameters(self, call_def):
        """
        Return list function parameters, prepared for sublime completion.
        Tuple contains parameter name and default value
        """

        if not call_def:
            return []

        params = []
        for param in call_def.params:
            cleaned_param = param.get_code().strip()
            if '*' in cleaned_param or cleaned_param == 'self':
                continue

            params.append([s.strip() for s in cleaned_param.split('=')])

        return params


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
            self._check()
            time.sleep(self.delta)

        self.server.shutdown()

    def _check(self):
        """Check for the ST3 pid
        """

        with self.server.locker:
            if time.time() - self.server.last_call > 1800:
                # is now more than 30 minutes of innactivity
                self.server.logger.info(
                    'detected inactivity for more than 30 minutes...'
                    'shuting down...'
                )
                self.die = True

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
            if not PID in output:
                self.server.logger.info(
                    'process {0} doe snot exists stopping server...'.format(
                        PID
                    )
                )
                self.die = True


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
        server = ThreadedJSONServer(('localhost', port), JSONHandler)
        logger.info(
            'Anaconda Server started in port {0} with cache dir {1}{2}'.format(
                port, jedi.settings.cache_directory,
                ' and extra paths {0}'.format(
                    options.extra_paths
                ) if options.extra_paths is not None else ''
            )
        )
    except Exception as error:
        logger.error(error)
        sys.exit(-1)

    # server = socketserver.TCPServer(('localhost', port), JSONHandler)
    server.logger = logger

    # start PID checker thread
    checker = Checker(server)
    checker.start()

    # start the server
    server.serve_forever()
