# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import json
import time
import errno
import logging
import threading
import traceback
from logging import handlers
from optparse import OptionParser

if sys.version_info[0] == 2:
    import SocketServer as socketserver
else:
    import socketserver

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

import jedi
from linting import linter
from contexts import json_decode


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

            logger.info(
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
                    logger.error('Error [32]Broken PIPE Killing myself... ')
                    self.shutdown()
                    sys.exit()
            except Exception as error:
                logger.info('Exception: {0}'.format(error))
                log_traceback()
        else:
            logger.error(
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
            data.extend([
                ('{0}\t{1}'.format(comp.name, comp.type), comp.name)
                for comp in completions
            ])
            result = {'success': True, 'completions': data}
        except Exception as error:
            result = {
                'success': False,
                'error': str(error),
                'tb': get_log_traceback()
            }

        print(result)
        self.wfile.write('{}\r\n'.format(json.dumps(result)))

    def goto(self):
        """Goto a Python definition
        """

        try:
            definitions = self.script.goto_assignments()
            if all(d.type == 'import' for d in definitions):
                definitions = self.script.get_definition()
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

        usages = self.script.usages()
        self.wfile.write('{}\r\n'.format(json.dumps({
            'success': True, 'usages': [
                (i.module_path, i.line, i.column)
                for i in usages if not i.in_builtin_module()
            ]
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
            if not os.path.exists('/proc/' + PID):
                self.server.logger.info(
                    'process {0} does not exists stopping server...'.format(
                        PID
                    )
                )
                self.die = True
        elif os.name == 'nt':
            try:
                from win32com.client import GetObject
                pid = sys.argv[2]
                WMI = GetObject('winmgmts:')
                proc = WMI.InstancesOf('Win32_Process')

                if pid not in [p.Properties_('ProcessID').Value for p in proc]:
                    self.die = True
            except:
                pass


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

    return ''.join(error)

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
