# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda PyLint wrapper
"""

import sys
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

    def __init__(self, filename):
        self.filename = filename
        self.exit = sys.exit
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
            args = "--msg-template={msg_id}:{line}:{msg} -r n".split(' ')

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
                ign, module = error.split('************* Module ')
                if not module in self.filename:
                    continue
            else:
                code, line, message = error.split(':', 2)
                errors[self._map_code(code)[0]].append({
                    'line': line,
                    'code': self._map_code(code)[1],
                    'message': message
                })

        return errors

    def _map_code(self, code):
        """Map the given code to fit Anaconda codes
        """

        mapping = {'C': 'V', 'R': 'W', 'E': 'E', 'F': 'E', 'W': 'W'}
        return (mapping[code[0]], code[1:])


if __name__ == '__main__':
    l = PyLinter(sys.argv[1])
    print(l.parse_errors())
