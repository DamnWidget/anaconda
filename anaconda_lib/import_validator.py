# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda imports validator
"""

import os
import sys
import functools


def sys_append(func):

    @functools.wraps(func)
    def wrapper(self, module_line):
        sys.path.append(self.filepath)
        result = func(self, module_line)
        sys.path.remove(sys.path[len(sys.path)-1])
        return result

    return wrapper


class Validator:
    """Try to import whatever import that is in the given source
    """

    def __init__(self, source, filename):
        self.source = source
        self.errors = []
        self.filepath = '.'
        if filename is not None:
            self.filepath = os.path.dirname(filename)

    def is_valid(self):
        """Determine if the source imports are valid or not
        """

        for line, lineno in self._extract_imports():
            if not self._validate_import(line):
                self.errors.append((line, lineno))

        return not self.errors

    @sys_append
    def _validate_import(self, module_line):
        """Try to validate the given import line
        """

        # we don't want to mess with sublime text runtime interpreter
        if 'sublime' in module_line:
            return True

        # maybe we don't want to do QA there
        if 'noqa' in module_line:
            return True

        # relative imports doesn't works so lets do a trick
        line = []
        for word in module_line.split():
            line.append(word[1:] if word.startswith('.') else word)

        line = ' '.join(line)
        c = compile(line, '<string>', 'single')
        try:
            exec(c)
        except (ImportError, ValueError, SystemError) as error:
            print(error)
            return False

        return True

    def _extract_imports(self):
        """Extract imports from the source
        """

        found = []
        lineno = 1
        for line in self.source.splitlines():
            l = line.strip()
            if l.startswith('import ') or l.startswith('from '):
                found.append((l, lineno))
            lineno += 1

        return found
