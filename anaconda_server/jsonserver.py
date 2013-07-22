# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import json
import logging
import threading
from time import sleep
from logging import handlers
from optparse import OptionParser

if sys.version_info[0] == 2:
    import SocketServer as socketserver
else:
    import socketserver

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

import jedi
from contexts import json_decode


class ThreadedJSONServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threading JSON Server
    """

    pass


class JSONHandler(socketserver.StreamRequestHandler):
    """Handler Class for the Anaconda JSON server
    """

    def handle(self):
        """This function handles requests from anaconda plugin
        """

        with json_decode(self.rfile.readline().strip()) as self.data:
            self.server.logger.info(
                '{0} requests: {1}'.format(self.client_address[0], self.data)
            )

        if type(self.data) is dict:
            try:
                getattr(self, self.data.pop('method'))(**self.data)
            except AttributeError as error:
                self.server.logger.debug('Exception: {0}'.format(error))
        else:
            self.server.logger.error(
                '{0} sent something that I dont undertand: {1}'.format(
                    self.client_address[0], self.data
                )
            )

    def autocomplete(self, source, line, offset, file='', encoding='utf-8'):
        """Return Jedi completions
        """

        script = jedi.Script(
            source, int(line), int(offset), file, encoding
        )

        completions = script.completions()
        self.wfile.write('{}\r\n'.format(json.dumps({
            'success': True, 'completions': [
                '{0}\t{1}'.format(c.name, c.type) for c in completions
            ]
        })))


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
            sleep(self.delta)

        self.server.shutdown()

    def _check(self):
        """Check for the ST3 pid
        """

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


def getLogger(path):
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

    logger = getLogger(jedi.settings.cache_directory)
    logger.info(
        'Anaconda Server started in port {0} with cache dir {1}{2}'.format(
            port, jedi.settings.cache_directory,
            ' and extra paths {0}'.format(
                options.extra_paths
            ) if options.extra_paths is not None else ''
        )
    )

    server = ThreadedJSONServer(('localhost', port), JSONHandler)

    # server = socketserver.TCPServer(('localhost', port), JSONHandler)
    server.logger = logger

    # start PID checker thread
    checker = Checker(server)
    checker.start()

    # start the server
    server.serve_forever()
