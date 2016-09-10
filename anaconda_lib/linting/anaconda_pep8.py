# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os

import pycodestyle as pep8
from linting import linter


class Pep8Error(linter.LintError):
    """PEP-8 linting error class
    """

    def __init__(self, filename, loc, offset, code, text, level='E'):
        ct_tuple = (code, text)
        err_str = '[{0}] PEP 8 (%s): %s'.format(level)
        super(Pep8Error, self).__init__(
            filename, loc, level, err_str, ct_tuple, offset=offset, text=text
        )


class Pep8Warning(linter.LintError):
    """PEP-8 lintng warning class
    """

    def __init__(self, filename, loc, offset, code, text, level='W'):
        ct_tuple = (code, text)
        err_str = '[{0}] PEP 8 (%s): %s'.format(level)
        super(Pep8Warning, self).__init__(
            filename, loc, level, err_str, ct_tuple, offset=offset, text=text
        )


class Pep8Linter(linter.Linter):
    """Linter for pep8 Linter
    """

    def lint(self, settings, code, filename):
        """Run the pep8 code checker with the given options
        """

        errors = []
        check_params = {
            'ignore': settings.get('pep8_ignore', []),
            'max_line_length': settings.get(
                'pep8_max_line_length', pep8.MAX_LINE_LENGTH
            ),
            'levels': settings.get('pep8_error_levels', {
                'E': 'W', 'W': 'V', 'V': 'V'
            })

        }
        errors.extend(self.check(
            code, filename, settings.get('pep8_rcfile'), **check_params
        ))

        return self.parse(errors)

    def check(self, code, filename, rcfile, ignore, max_line_length, levels):
        """Check the code with pyflakes to find errors
        """

        messages = []
        _lines = code.split('\n')

        if _lines:
            class AnacondaReport(pep8.BaseReport):
                """Helper class to report PEP8 problems
                """

                def error(self, line_number, offset, text, check):
                    """Report an error, according to options
                    """

                    col = line_number
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
                        filename, col, offset, code, message, levels[code[0]]
                    ))

                    return code

            params = {'reporter': AnacondaReport}
            if not rcfile:
                _ignore = ignore
                params['ignore'] = _ignore
            else:
                params['config_file'] = os.path.expanduser(rcfile)

            options = pep8.StyleGuide(**params).options
            if not rcfile:
                options.max_line_length = max_line_length

            good_lines = [l + '\n' for l in _lines]
            good_lines[-1] = good_lines[-1].rstrip('\n')

            if not good_lines[-1]:
                good_lines = good_lines[:-1]

            pep8.Checker(filename, good_lines, options=options).check_all()

        return messages

    def parse(self, errors):
        errors_list = []
        if errors is None:
            return errors_list

        self.sort_errors(errors)
        for error in errors:
            error_level = self.prepare_error_level(error)
            message = error.message.capitalize()
            offset = error.offset

            error_data = {
                'underline_range': True,
                'level': error_level,
                'lineno': error.lineno,
                'offset': offset,
                'message': message,
                'raw_error': str(error)
            }
            errors_list.append(error_data)

        return errors_list
