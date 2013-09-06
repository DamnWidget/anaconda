# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
The majority of this code is based/inspired or directly taken from
SublimeLinter plugin. Because that, SublimeLinter license file has
been added to this package.

This doesn't meant that anaconda is a fork of SublimeLinter in any
way or that anaconda is going to be updated with latest SublimeLinter
updates. Anaconda and SublimeLinter are two completely separated
projects but they did a great job with SublimeLinter so we are reusing
part of their plugin to lint our Python scripts.

The main difference between SublimeLinter linting and anaconda one is
that the former lints always for Python3.3 even if we are coding in
a Python 2 project. Anaconda lints for the configured Python environment
"""

import os
import re
import sys
sys.path.insert(0, os.path.dirname(__file__))

import _ast

import pep8
import pyflakes.checker as pyflakes


if sys.version_info < (2, 7):
    def cmp_to_key(mycmp):
        """Convert a cmp= function into a key= function
        """

        class K(object):
            __slots__ = ['obj']

            def __init__(self, obj, *args):
                self.obj = obj

            def __lt__(self, other):
                return mycmp(self.obj, other.obj) < 0

            def __gt__(self, other):
                return mycmp(self.obj, other.obj) > 0

            def __eq__(self, other):
                return mycmp(self.obj, other.obj) == 0

            def __le__(self, other):
                return mycmp(self.obj, other.obj) <= 0

            def __ge__(self, other):
                return mycmp(self.obj, other.obj) >= 0

            def __ne__(self, other):
                return mycmp(self.obj, other.obj) != 0

            def __hash__(self):
                raise TypeError('hash not implemented')

        return K
else:
    from functools import cmp_to_key


pyflakes.messages.Message.__str__ = (
    lambda self: self.message % self.message_args
)


class LintError(pyflakes.messages.Message):
    """Lint error base class
    """

    def __init__(self, filename, loc, level, message, message_args, **kwargs):
        super(LintError, self).__init__(filename, loc)

        self.level = level
        self.message = message
        self.message_args = message_args
        offset = kwargs.get('offset')
        text = kwargs.get('text')

        if offset is not None:
            self.offset = offset
        if text is not None:
            self.text = text


class Pep8Error(LintError):
    """
    Lint error clss for PEP-8 errors
    PEP-8 errors are treated as Warnings
    """

    def __init__(self, filename, loc, offset, code, text):
        super(Pep8Error, self).__init__(
            filename, loc, 'W', '[W] PEP 8 (%s): %s', (code, text),
            offset=offset, text=text
        )


class Pep8Warning(LintError):
    """
    Lint error clss for PEP-8 warnings
    PEP-8 warnings are treated as violations
    """

    def __init__(self, filename, loc, offset, code, text):
        super(Pep8Warning, self).__init__(
            filename, loc, 'V', '[V] PEP 8 (%s): %s', (code, text),
            offset=offset, text=text
        )


class PythonError(LintError):
    """Python errors class
    """

    def __init__(self, filename, loc, text):
        super(PythonError, self).__init__(
            filename, loc, 'E', '[E] %r', (text,), text=text
        )


class OffsetError(LintError):

    def __init__(self, filename, loc, text, offset):
        super(OffsetError, self).__init__(
            filename, loc, 'E', '[E] %s', (text,),
            offset=offset + 1, text=text
        )


class Linter(object):
    """Linter class for Anaconda's Python linter
    """

    def __init__(self):

        self.enabled = False

    def pyflakes_check(self, code, filename, ignore=None):
        """Check the code with pyflakes to find errors
        """

        class FakeLoc:
            lineno = 0

        try:
            tree = compile(str(code), filename, 'exec', _ast.PyCF_ONLY_AST)
        except (SyntaxError, IndentationError) as value:
            return self._handle_syntactic_error(code, filename, value)
        except ValueError as error:
            return [PythonError(filename, FakeLoc(), error.args[0])]
        else:
            # the file is syntactically valid, check it now
            if ignore is not None:
                _magic_globals = pyflakes._MAGIC_GLOBALS
                pyflakes._MAGIC_GLOBALS += ignore

            w = pyflakes.Checker(tree, filename)

            if ignore is not None:
                pyflakes._MAGIC_GLOBALS = _magic_globals

            return w.messages

    def pep8_check(self, code, filename, ignore, max_line_length):
        """Check the code with pep8 to find PEP 8 errors
        """

        messages = []
        _lines = code.split('\n')

        if _lines:
            class FakeCol:
                """Fake class to represent a col object for PyFlakes
                """

                def __init__(self, line_number):
                    self.lineno = line_number

            class SublimeLinterReport(pep8.BaseReport):
                """Helper class to report PEP 8 problems
                """

                def error(self, line_number, offset, text, check):
                    """Report an error, according to options
                    """
                    col = FakeCol(line_number)
                    code = text[:4]
                    message = text[5:]

                    if self._ignore_code(code):
                        return

                    if code in self.counters:
                        self.counters[code] += 1
                    else:
                        self.counters[code] = 1
                        self.messages[code] = message

                    if code in self.expected:
                        return

                    self.file_errors += 1
                    self.total_errors += 1

                    pep8_error = code.startswith('E')
                    klass = Pep8Error if pep8_error else Pep8Warning
                    messages.append(klass(
                        filename, col, offset, code, message
                    ))

                    return code

            _ignore = ignore + pep8.DEFAULT_IGNORE.split(',')
            options = pep8.StyleGuide(
                reporter=SublimeLinterReport, ignore=_ignore).options
            options.max_line_length = max_line_length

            good_lines = [l + '\n' for l in _lines]
            good_lines[-1] = good_lines[-1].rstrip('\n')

            if not good_lines[-1]:
                good_lines = good_lines[:-1]

            pep8.Checker(filename, good_lines, options=options).check_all()

        return messages

    def run_linter(self, settings, code, filename):
        """Check the code to find errors
        """

        errors = []

        if settings.get("pep8", True):
            check_params = {
                'ignore': settings.get('pep8_ignore', []),
                'max_line_length': settings.get('pep8_max_line_length',
                                                 pep8.MAX_LINE_LENGTH)
            }
            errors.extend(self.pep8_check(
                code, filename, **check_params)
            )

        pyflakes_ignore = settings.get('pyflakes_ignore', None)
        pyflakes_disabled = settings.get('pyflakes_disabled', False)

        if not pyflakes_disabled:
            errors.extend(self.pyflakes_check(code, filename, pyflakes_ignore))

        return self.parse_errors(errors)

    def parse_errors(self, errors):
        """Parse errors returned from the PyFlakes and pep8 libraries
        """

        errors_list = []
        if errors is None:
            return errors_list

        errors.sort(key=cmp_to_key(lambda a, b: a.lineno < b.lineno))

        for error in errors:
            error_level = 'W' if not hasattr(error, 'level') else error.level
            message = '{0}{1}'.format(
                error.message[0].upper(), error.message[1:]
            )

            offset = None
            if hasattr(error, 'offset'):
                offset = error.offset

            error_data = {
                'pep8': False,
                'level': error_level,
                'lineno': error.lineno,
                'offset': offset,
                'message': message,
                'raw_error': str(error)
            }

            if isinstance(error, (Pep8Error, Pep8Warning, OffsetError)):
                error_data['pep8'] = True
                errors_list.append(error_data)
            elif isinstance(
                error, (
                    pyflakes.messages.RedefinedWhileUnused,
                    pyflakes.messages.UndefinedName,
                    pyflakes.messages.UndefinedExport,
                    pyflakes.messages.UndefinedLocal,
                    pyflakes.messages.Redefined,
                    pyflakes.messages.UnusedVariable)):
                regex = (
                    r'((and|or|not|if|elif|while|in)\s+|[+\-*^%%<>=\(\{{])*\s'
                    '*(?P<underline>[\w\.]*{0}[\w]*)'.format(re.escape(
                        error.message_args[0]
                    ))
                )
                error_data['regex'] = regex
                errors_list.append(error_data)
            elif isinstance(error, pyflakes.messages.ImportShadowedByLoopVar):
                regex = 'for\s+(?P<underline>[\w]*{0}[\w*])'.format(
                    re.escape(error.message_args[0])
                )
                error_data['regex'] = regex
                errors_list.append(error_data)
            elif isinstance(
                error, (
                    pyflakes.messages.UnusedImport,
                    pyflakes.messages.ImportStarUsed)):
                if isinstance(error, pyflakes.messages.ImportStarUsed):
                    word = '*'
                else:
                    word = error.message_args[0]

                linematch = '(from\s+[\w_\.]+\s+)?import\s+(?P<match>[^#;]+)'
                r = '(^|\s+|,\s*|as\s+)(?P<underline>[\w]*{0}[\w]*)'.format(
                    re.escape(word)
                )
                error_data['regex'] = r
                error_data['linematch'] = linematch
                errors_list.append(error_data)
            elif isinstance(error, pyflakes.messages.DuplicateArgument):
                regex = 'def [\w_]+\(.*?(?P<underline>[\w]*{0}[\w]*)'.format(
                    re.escape(error.message_args[0])
                )
                error_data['regex'] = regex
                errors_list.append(error_data)
            elif isinstance(error, pyflakes.messages.LateFutureImport):
                pass
            elif isinstance(error, PythonError):
                print(error)
            else:
                print('Oops, we missed an error type!', type(error))

        return errors_list

    def _handle_syntactic_error(self, code, filename, value):
        """Handle PythonError and OffsetError
        """

        msg = value.args[0]

        (lineno, offset, text) = value.lineno, value.offset, value.text

        if text is None:    # encoding problems
            if msg.startswith('duplicate argument'):
                arg = msg.split(
                    'duplicate argument ', 1)[1].split(' ', 1)[0].strip('\'"')
                error = pyflakes.messages.DuplicateArgument(
                    filename, lineno, arg
                )
            else:
                error = PythonError(filename, value, msg)
        else:
            line = text.splitlines()[-1]

            if offset is not None:
                offset = offset - (len(text) - len(line))

            if offset is not None:
                error = OffsetError(filename, value, msg, offset)
            else:
                error = PythonError(filename, value, msg)

        return [error]
