# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda McCabe
"""

import ast

from .mccabe import McCabeChecker


class AnacondaMcCabe(object):
    """Wrapper object around McCabe python script
    """

    checker = McCabeChecker

    def __init__(self, code, filename):
        self.code = code
        self.filename = filename

    @property
    def tree(self):
        """Compile and send back an AST if buffer is able to be parsed
        """

        try:
            code = self.code.encode('utf8') + b'\n'
            return compile(code, self.filename, 'exec', ast.PyCF_ONLY_AST)
        except SyntaxError:
            return None

    def get_code_complexity(self, threshold=7):
        """Get the code complexity for the current buffer and return it
        """

        if self.tree is not None:
            self.checker.max_complexity = threshold
            return self.parse(self.checker(self.tree, self.filename).run())

        return None

    def parse(self, complexities):
        """
        Parse the given list of complexities to something that anaconda
        understand and is able to handle
        """

        errors = []
        for complexity in complexities:
            errors.append({
                'line': int(complexity[0]),
                'offset': int(complexity[1] + 1),
                'code': complexity[2].split(' ', 1)[0],
                'message': complexity[2].split(' ', 1)[1]
            })

        return errors
