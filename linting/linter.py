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
part of their plugin to lint our Python scripts.Python

The main difference between SublimeLinter linting and anaconda one is
that the former lints always for Python3.3 even if we are coding in
a Python 2 project. Anaconda lints for the configured Python environment
"""

import re
import _ast
import pep8
from functools import cmp_to_key

import pyflakes.checker as pyflakes

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
            filename, loc, 'W', '[W] PEP 8 ({0}): {1}'.format(code, text),
            offset=offset, text=text
        )


class Pep8Warning(LintError):
    """
    Lint error clss for PEP-8 warnings
    PEP-8 warnings are treated as violations
    """

    def __init__(self, filename, loc, offset, code, text):
        super(Pep8Warning, self).__init__(
            filename, loc, 'V', '[V] PEP 8 ({0}): {1}'.format(code, text),
            offset=offset, text=text
        )


class PythonError(LintError):
    """Python errors class
    """

    def __init__(self, filename, loc, text):
        super(PythonError, self).__init__(
            filename, loc, 'E', '[E] {0!r}'.format(text), text=text
        )


class OffsetError(LintError):

    def __init__(self, filename, loc, text, offset):
        super(OffsetError, self).__init__(
            filename, loc, 'E', '[E] {0!r}'.format(text),
            offset=offset + 1, text=text
        )


class Linter(object):
    """Linter class for Anaconda's Python linter
    """

    def __init__(self, config):

        self.enabled = False

    def pyflakes_check(self, code, filename, ignore=None):
        """Check the code with pyflakes to find errors
        """

        try:
            tree = compile(code, filename, 'exec', _ast.PyCF_ONLY_AST)
        except (SyntaxError, IndentationError) as value:
            return self._handle_syntactic_error(code, filename, value)
        except ValueError as error:
            return [PythonError(filename, 0, error.args[0])]
        else:
            # the file is syntactically valid, check it now
            if ignore is not None:
                _magic_globals = pyflakes._MAGIC_GLOBALS
                pyflakes._MAGIC_GLOBALS += ignore

            w = pyflakes.Checker(tree, filename)

            if ignore is not None:
                pyflakes._MAGIC_GLOBALS = _magic_globals

            return w.messages

    def pep8_check(self, code, filename, ignore=None):
        """Check the code with pep8 to find PEP 8 errors
        """

        messages = []
        _lines = code.split('\n')

        if _lines:
            class SublimeLinterReport(pep8.BaseReport):
                """Helper class to report PEP 8 problems
                """

                def error(self, line_number, offset, text, check):
                    """Report an error, according to options
                    """
                    code = text[:4]
                    message = text[5:]

                    if self._ignore_code(code):
                        return

                    if code in self.counters:
                        self.counters[code] += 1
                    else:
                        self.counters[code] = 1
                        self.messages[code] = message

                    if code in self.excepted:
                        return

                    self.file_errors += 1
                    self.total_errors += 1

                    pep8_error = code.startswith('E')
                    klass = Pep8Error if pep8_error else Pep8Warning
                    messages.append(klass(
                        filename, line_number, offset, code, message
                    ))

                    return code

            _ignore = ignore + pep8.DEFAULT_IGNORE.split(',')
            options = pep8.StyleGuide(
                reporter=SublimeLinterReport, ignore=_ignore).options
            options.max_line_length = pep8.MAX_LINE_LENGTH

            good_lines = [l + '\n' for l in _lines]
            good_lines[-1] = good_lines[-1].rstrip('\n')

            if not good_lines[-1]:
                good_lines = good_lines[:-1]

            try:
                pep8.Checker(filename, good_lines, options=options).check_all()
            except Exception as e:
                print("An exception occured when running pep8 checker: %s" % e)

        return messages

    def built_in_check(self, settings, code, filename, vid):
        """Check the code to find errors
        """

        errors = []

        if settings.get("pep8", True):
            errors.extend(self.pep8_check(
                code, filename, ignore=settings.get('pep8_ignore', []))
            )

        pyflakes_ignore = settings.get('pyflakes_ignore', None)
        pyflakes_disabled = settings.get('pyflakes_disabled', False)

        if not pyflakes_disabled:
            errors.extend(self.pyflakes_check(code, filename, pyflakes_ignore))

        return errors

    def _handle_syntactic_error(self, code, filename, value):
        """Handle PythonError and OffsetError
        """

        msg = value.args[0]

        (lineno, offset, text) = value.lineno, value.offset, value.text

        if text is None:    # encoding problems
            if msg.startswith('duplicate argument'):
                arg = msg.split('duplicate argument', 1)[1].split(' ', 1)
                error = pyflakes.messages.DuplicateArgument(
                    filename, lineno, arg[0].strip('\'"')
                )
            else:
                error = PythonError(filename, lineno, msg)
        else:
            line = text.splilines()[-1]

            if offset is not None:
                offset = offset - (len(text) - len(line))
                error = OffsetError(filename, lineno, msg, offset)
            else:
                error = PythonError(filename, lineno, msg)

        return [error]

    def _jsonize(self, errors, vid, ignore_star=False):
        """Convert a list of PyFlakes and PEP-8 errors into JSON
        """

        errors.sort(key=cmp_to_key(lambda a, b: a.lineno < b.lineno))
        for error in errors:
            error_level = 'W' if not hasattr(error, 'level') else error.level
            messages, underlines = self._get_errors_level(error_level, vid)

            if type(error) is pyflakes.messages.ImportStarUsed and ignore_star:
                continue

    def _get_errors_level(self, error_level, vid):
        """Return back the right error levels for messages and underlines
        """

        messages, underlines = self.error_level_mapper.get(error_level)
        return messages[vid], underlines[vid]
