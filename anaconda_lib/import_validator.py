# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda imports validator
"""

from jedi import Script


class Validator:
    """Try to import whatever import that is in the given source
    """

    def __init__(self, source, filename):
        self.source = source
        self.errors = []  # type: List
        self.filename = filename

    def is_valid(self):
        """Determine if the source imports are valid or not
        """

        for line, lineno in self._extract_imports():
            error, valid = self._validate_import(line, lineno)
            if not valid:
                self.errors.append((error, lineno))

        return not self.errors

    def _validate_import(self, module_line, lineno):
        """Try to validate the given iport line
        """

        if 'noqa' in module_line:
            return True

        error = []
        error_string = 'can\'t import {0}'
        valid = True
        for word in module_line.split():
            if word in ('from', 'import', 'as'):
                continue

            offset = int(module_line.find(word) + len(word) / 2)
            s = Script(self.source, lineno, offset, self.filename)
            if not self.filename:
                s = Script(module_line, 1, offset)

            if not s.goto_assignments():
                if valid is True:
                    valid = False
                error.append(word)

        err = '' if valid else error_string.format(' '.join(error))
        return err, valid

    def _extract_imports(self):
        """Extract imports from the source
        """

        found = []
        lineno = 1
        buffer_found = []  # type: List
        in_docstring = False
        for line in self.source.splitlines():
            if self.__detect_docstring(line):
                if in_docstring:
                    in_docstring = False
                else:
                    in_docstring = True
                lineno += 1
                continue
            else:
                line = line.strip()
                if len(buffer_found) > 0:
                    if ')' in line:
                        buffer_found.append(line.replace(')', '').strip())
                        found.append((' '.join(buffer_found), lineno))
                        buffer_found = []
                    else:
                        buffer_found.append(line)
                else:
                    if self.__detect_docstring(line):
                        continue
                if line.startswith('import ') or line.startswith('from '):
                    if '(' in line:
                        buffer_found.append(line.replace('(', '').strip())
                    else:
                        found.append((line, lineno))
            lineno += 1
        return found

    def __detect_docstring(self, line):
        """Detects if there is a docstring
        """

        if '"""' in line or "'''" in line:
            return True

        return False
