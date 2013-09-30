# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda PyLint wrapper
"""

import os
import sys
import logging

if sys.version_info >= (3, 0):
    from io import StringIO
else:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
        assert StringIO

from pylint import lint
from pylint.__pkginfo__ import numversion


class PyLinter(object):
    """PyLinter class for Anaconda
    """

    def __init__(self, filename, rcfile):
        self.filename = filename
        self.exit = sys.exit
        self.rcfile = rcfile
        self.stdout = sys.stdout
        self.output = StringIO()

        sys.exit = lambda x: None
        sys.stdout = self.output

        self.execute()

    def execute(self):
        """Execute the linting process
        """

        if numversion < (1, 0, 0):
            args = '--include-ids=y -r n'.split(' ')
        else:
            args = '--msg-template={msg_id}:{line}:{column}:{msg} -r n'.split(
                ' ')

        if self.rcfile:
            args.append('--rcfile={0}'.format(os.path.expanduser(self.rcfile)))

        args.insert(0, self.filename)
        lint.Run(args)

    def parse_errors(self):
        """Parse the output given by PyLint
        """

        errors = {'E': [], 'W': [], 'V': []}
        data = self.output.getvalue()

        sys.exit = self.exit
        sys.stdout = self.stdout

        for error in data.splitlines():
            if '************* Module ' in error:
                _, module = error.split('************* Module ')
                if not module in self.filename:
                    continue
            else:
                offset = None
                try:
                    if numversion >= (1, 0, 0):
                        code, line, offset, message = error.split(':', 3)
                    else:
                        code, line, message = error.split(':', 2)
                except ValueError as exception:
                    logging.debug(
                        'unhandled exception in PyLinter parse_errors '
                        'this is a non fatal error: {0}'.format(exception)
                    )
                    logging.debug(
                        'the error string that raised this exception was: '
                        '{0}, please, report this in the GitHub site'.format(
                            error
                        )
                    )
                    continue

                if numversion < (1, 0, 0):
                    try:
                        line, offset = line.split(',')
                    except ValueError:
                        # seems like some versions (or packagers) of pylint
                        # prior to 1.0.0 adds offset to the output but others
                        # doesn't
                        pass

                errors[self._map_code(code)[0]].append({
                    'line': int(line),
                    'offset': offset,
                    'code': self._map_code(code)[1],
                    'message': '[{0}] {1}'.format(
                        self._map_code(code)[1], message
                    )
                })

        return errors

    def _map_code(self, code):
        """Map the given code to fit Anaconda codes
        """

        mapping = {'C': 'V', 'E': 'E', 'F': 'E', 'I': 'V', 'R': 'W', 'W': 'W'}
        return (mapping[code[0]], code[1:])
