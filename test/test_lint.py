
# Copyright (C) 2012-2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sys

from handlers.python_lint_handler import PythonLintHandler

PYTHON3 = sys.version_info >= (3, 0)


class TestLint(object):
    """Linting test suite
    """

    _lintable_code = '''
def f():
    a = 1
    [1 for a, b in [(1, 2)]]
    '''

    _lintable_docstring = '''
def f():
    """This is a docst
    ring"""'''

    _import_validator_code = '''
import idontexists


def main():
    idontexists('Hello World!')
    '''

    def setUp(self):
        self._settings = {
            'use_pyflakes': False, 'use_pylint': False, 'use_pep257': False,
            'pep8': False, 'vapidate_imports': False
        }

    def test_pyflakes_lint(self):
        handler = PythonLintHandler('lint', None, 0, 0, self._check_pyflakes)
        self._settings['use_pyflakes'] = True
        handler.lint(self._settings, self._lintable_code)

    def test_pyflakes_ignore(self):
        handler = PythonLintHandler('lint', None, 0, 0, self._check_pyflakes_ignore)  # noqa
        self._settings['use_pyflakes'] = True
        self._settings['pyflakes_ignore'] = 'F841'

    def test_pep8_lint(self):
        self._settings['pep8'] = True
        handler = PythonLintHandler('lint', None, 0, 0, self._check_pep8)
        handler.lint(self._settings, self._lintable_code)

    def test_pep8_ignores(self):
        self._settings['pep8'] = True
        self._settings['pep8_ignore'] = ['W293']
        handler = PythonLintHandler('lint', None, 0, 0, self._check_pep8_ignores)  # noqa
        handler.lint(self._settings, self._lintable_code)

    def test_pep8_max_line_lenght(self):
        self._settings['pep8'] = True
        self._settings['pep8_max_line_length'] = 120
        handler = PythonLintHandler('lint', None, 0, 0, self._check_pep8_max_line_length)  # noqa
        handler.lint(self._settings, 'a = \'this is a very long string: {0}\'\n'.format('a' * 80))  # noqa

    def test_pep257_lint(self):
        self._settings['use_pep257'] = True
        handler = PythonLintHandler('lint', None, 0, 0, self._check_pep257)
        handler.lint(self._settings, self._lintable_docstring, '')

    def test_pep257_ignores(self):
        self._settings['use_pep257'] = True
        self._settings['pep257_ignore'] = ['D100', 'D400', 'D209', 'D205', 'D401']  # noqa
        handler = PythonLintHandler('lint', None, 0, 0, self._check_pep257_ignores)  # noqa
        handler.lint(self._settings, self._lintable_docstring, '')

    def test_import_validator(self):
        self._settings['validate_imports'] = True
        handler = PythonLintHandler('lint', None, 0, 0, self._check_validate_imports)  # noqa
        handler.lint(self._settings, self._import_validator_code, '')

    def _check_pyflakes(self, result):
        assert result['success'] is True
        assert len(result['errors']) == 1
        assert result['errors'][0]['level'] == 'W'
        err = 'list comprehension redefines \'a\' from line 3' \
            if not PYTHON3 else 'local variable \'a\' is assigned to but never used'  # noqa
        assert result['errors'][0]['raw_error'] == err
        assert result['errors'][0]['underline_range'] is False
        assert result['uid'] == 0
        assert result['vid'] == 0

    def _check_pep8(self, result):
        assert result['success'] is True
        assert len(result['errors']) == 2
        error1 = result['errors'][0]
        assert error1['raw_error'] == '[V] PEP 8 (W391): blank line at end of file'  # noqa
        assert error1['level'] == 'V'
        assert error1['underline_range'] is True
        error2 = result['errors'][1]
        assert error2['raw_error'] == '[V] PEP 8 (W293): blank line contains whitespace'  # noqa
        assert error2['level'] == 'V'
        assert error2['underline_range'] is True
        assert result['uid'] == 0
        assert result['vid'] == 0

    def _check_pep8_ignores(self, result):
        assert result['success'] is True
        assert len(result['errors']) == 1
        error1 = result['errors'][0]
        assert error1['raw_error'] == '[V] PEP 8 (W391): blank line at end of file'  # noqa
        assert error1['level'] == 'V'
        assert error1['underline_range'] is True
        assert result['uid'] == 0
        assert result['vid'] == 0

    def _check_pep8_max_line_length(self, result):
        assert result['success'] is True
        assert len(result['errors']) == 0
        assert result['uid'] == 0
        assert result['vid'] == 0

    def _check_pyflakes_ignore(self, result):
        assert result['success'] is True
        assert len(result['errors']) == 0
        assert result['uid'] == 0
        assert result['vid'] == 0

    def _check_pep257(self, result):
        assert result['success'] is True
        assert len(result['errors']) == 5
        raw_errors = [r['raw_error'] for r in result['errors']]
        assert '[V] PEP 257 (D100): Missing docstring in public module' in raw_errors  # noqa
        assert '[V] PEP 257 (D209): Multi-line docstring closing quotes should be on a separate line' in raw_errors  # noqa
        assert '[V] PEP 257 (D205): 1 blank line required between summary line and description (found 0)' in raw_errors  # noqa
        assert '[V] PEP 257 (D400): First line should end with a period (not \'t\')' in raw_errors  # noqa
        assert '[V] PEP 257 (D401): First line should be in imperative mood (\'Thi\', not \'This\')' in raw_errors  # noqa

        error1, error2, error3, error4, error5 = result['errors']
        assert (error1['level'], error2['level'], error3['level'], error4['level'], error5['level']) == ('V', 'V', 'V', 'V', 'V')  # noqa
        assert result['uid'] == 0
        assert result['vid'] == 0

    def _check_pep257_ignores(self, result):
        assert result['success'] is True
        assert len(result['errors']) == 0
        assert result['uid'] == 0
        assert result['vid'] == 0

    def _check_validate_imports(self, result):
        assert result['success'] is True
        assert len(result['errors']) == 1
        assert result['errors'][0]['raw_error'] == "[E] ImportValidator (801): can't import idontexists"  # noqa
        assert result['errors'][0]['code'] == 801
        assert result['errors'][0]['level'] == 'E'
        assert result['errors'][0]['underline_range'] is True
        assert result['uid'] == 0
        assert result['vid'] == 0
