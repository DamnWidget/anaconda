# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import re
import _ast

from linting import linter
import pyflakes.checker as pyflakes


pyflakes.messages.Message.__str__ = (
    lambda self: self.message % self.message_args
)


class PyFlakesError(pyflakes.messages.Message):
    """Lint error base class
    """

    def __init__(self, filename, loc, level, message, message_args, **kwargs):
        super(PyFlakesError, self).__init__(filename, loc)

        self.level = level
        self.message = message
        self.message_args = message_args


class PyFlakesLinter(linter.Linter):
    """Linter for PyFlakes Linter
    """

    def lint(self, settings, code, filename):
        """Run the pyflakes code checker with the given options
        """

        errors = []
        pyflakes_ignore = settings.get('pyflakes_ignore', None)
        pyflakes_disabled = settings.get('pyflakes_disabled', False)
        explicit_ignore = settings.get('pyflakes_explicit_ignore', [])

        if not pyflakes_disabled and not settings.get('use_pylint'):
            errors.extend(self.check(code, filename, pyflakes_ignore))

        return self.parse(errors, explicit_ignore)

    def check(self, code, filename, ignore=None):
        """Check the code with pyflakes to find errors
        """

        class FakeLoc:
            lineno = 0

        try:
            fname = ''
            if filename is not None:
                fname = filename.encode('utf8') or ''
            code = code.encode('utf8') + b'\n'
            tree = compile(code, fname, 'exec', _ast.PyCF_ONLY_AST)
        except (SyntaxError, IndentationError):
            return self._handle_syntactic_error(code, filename)
        except ValueError as error:
            return [PyFlakesError(filename, FakeLoc(), 'E', error.args[0]), []]
        else:
            # the file is syntactically valid, check it now
            w = pyflakes.Checker(tree, filename, ignore)

            return w.messages

    def parse(self, errors, explicit_ignore):
        """Parse the errors returned from the PyFlakes library
        """

        error_list = []
        if errors is None:
            return error_list

        errors.sort(key=linter.cmp_to_key(lambda a, b: a.lineno < b.lineno))
        for error in errors:
            error_level = 'W' if not hasattr(error, 'level') else error.level
            message = error.message.capitalize()

            error_data = {
                'underline_range': False,
                'level': error_level,
                'lineno': error.lineno,
                'message': message,
                'raw_error': str(error)
            }
            if hasattr(error, 'offset'):
                error_data['offset'] = error.offset
            elif hasattr(error, 'col'):
                error_data['offset'] = error.col

            if (isinstance(error, (linter.OffsetError))):
                error_data['underline_range'] = True
                error_list.append(error_data)
            elif (isinstance(
                error, (
                    pyflakes.messages.RedefinedWhileUnused,
                    pyflakes.messages.RedefinedInListComp,
                    pyflakes.messages.UndefinedName,
                    pyflakes.messages.UndefinedExport,
                    pyflakes.messages.UndefinedLocal,
                    pyflakes.messages.UnusedVariable)) and
                    error.__class__.__name__ not in explicit_ignore):

                error_data['len'] = len(error.message_args[0])
                error_data['regex'] = (
                    r'((and|or|not|if|elif|while|in)\s+|[+\-*^%%<>=\(\{{])*\s'
                    '*(?P<underline>[\w\.]*{0}[\w]*)'.format(re.escape(
                        error.message_args[0]
                    ))
                )
                error_list.append(error_data)
            elif isinstance(error, pyflakes.messages.ImportShadowedByLoopVar):
                regex = 'for\s+(?P<underline>[\w]*{0}[\w*])'.format(
                    re.escape(error.message_args[0])
                )
                error_data['regex'] = regex
                error_list.append(error_data)
            elif (isinstance(
                error, (
                    pyflakes.messages.UnusedImport,
                    pyflakes.messages.ImportStarUsed)) and
                    error.__class__.__name__ not in explicit_ignore):
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
                error_list.append(error_data)
            elif (isinstance(error, pyflakes.messages.DuplicateArgument) and
                    error.__class__.__name__ not in explicit_ignore):
                regex = 'def [\w_]+\(.*?(?P<underline>[\w]*{0}[\w]*)'.format(
                    re.escape(error.message_args[0])
                )
                error_data['regex'] = regex
                error_list.append(error_data)
            elif isinstance(error, pyflakes.messages.LateFutureImport):
                pass
            elif isinstance(error, linter.PythonError):
                print(error)
            else:
                print(
                    'Ooops, we missed an error type for pyflakes', type(error)
                )

        return error_list
