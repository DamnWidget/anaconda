# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda imports validator
"""

import os
import sys
import logging
import functools

DEBUG = True


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
        parent_append = False
        for word in module_line.split():
            if word.startswith('..'):
                parent_append = True
                line.append(word[2:])
            elif word.startswith('.'):
                line.append(word[1:])
            else:
                line.append(word)

        line = ' '.join(line)
        if 'from  import' in line:  # this happens after strip: from . import ?
            line = line.replace('from  ', '').strip()

        if parent_append is True:
            path = self.filepath.rsplit('/', 1)[0]
            if path not in sys.path:
                sys.path.append(path)

        success = True
        c = compile(line, '<string>', 'single')
        try:
            exec(c)
        except (ImportError, ValueError, SystemError) as error:
            if 'sublime' in error:  # don't fuck up ST3 plugins development :)
                success = True
            else:
                if DEBUG:
                    logging.debug(error)
                success = False

        if parent_append is True:
            sys.path.remove(sys.path[len(sys.path)-1])
        return success

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
