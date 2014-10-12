# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda imports validator
"""

from jedi import Script


DEBUG = True


class Validator:
    """Try to import whatever import that is in the given source
    """

    def __init__(self, source, filename):
        self.source = source
        self.errors = []
        self.filename = filename

    def is_valid(self):
        """Determine if the source imports are valid or not
        """

        for line, lineno in self._extract_imports():
            error, valid = self._validate_import(line)
            if not valid:
                self.errors.append((error, lineno))

        return not self.errors

    def _validate_import(self, module_line):
        """Try to validate the given iport line
        """

        if 'noqa' in module_line:
            return True

        error = []
        error_string = 'can\'t import {}'
        valid = True
        for word in module_line.split():
            if word in ('from', 'import', 'as'):
                continue

            offset = module_line.find(word) + len(word) / 2
            if not Script(module_line, 1, offset, self.filename).goto():
                if valid is True:
                    valid = False
                error.append(word)

        return '' if valid else error_string.format(' '.join(error)), valid

    def _extract_imports(self):
        """Extract imports from the source
        """

        found = []
        lineno = 1
        buffer_found = []
        for line in self.source.splitlines():
            l = line.strip()
            if len(buffer_found) > 0:
                if ')' in l:
                    buffer_found.append(l.replace(')', '').strip())
                    found.append((' '.join(buffer_found), lineno))
                    buffer_found = []
                else:
                    buffer_found.append(l)
            else:
                if l.startswith('import ') or l.startswith('from '):
                    if '(' in l:
                        buffer_found.append(l.replace('(', '').strip())
                    else:
                        found.append((l, lineno))
            lineno += 1

        return found
