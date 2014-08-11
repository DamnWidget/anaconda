# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../anaconda_lib'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from anaconda_handler import AnacondaHandler
from linting.anaconda_pep8 import Pep8Linter
from commands import PyFlakes, PEP257, PEP8, PyLint
from linting.anaconda_pyflakes import PyFlakesLinter
from linting.anaconda_pep257 import PEP257 as AnacondaPep257

try:
    from linting.anaconda_pylint import PyLinter
    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False


class PythonLintHanler(AnacondaHandler):
    """Handle request to execute Python linting commands form the JsonServer
    """

    def __init__(self, command, data, uid, vid, callback, debug=False):
        self.uid = uid
        self.vid = vid
        self.data = data
        self.debug = debug
        self._callback = callback
        self.callback = self._merge_results
        self._register_command(command)
        self._linters = {
            'pyflakes': False, 'pylint': False, 'pep8': False, 'pep257': False
        }
        self._errors = []
        self._failures = []

    def lint(self, settings, code, filename):
        """This is called from the JsonServer
        """

        self._configure_linters(settings)
        for linter_name, expected in self._linters.items():
            if expected is True:
                func = getattr(self, linter_name)
                func(settings, code, filename)

        if len(self._errors) == 0:
            self._callback({
                'success': False,
                'errors': self._failures,
                'uid': self.uid,
                'vid': self.vid
            })
            return

        self._callback({
            'success': True,
            'errors': self._errors,
            'uid': self.uid,
            'vid': self.vid
        })

    def pyflakes(self, settings, code, filename):
        """Run the PyFlakes linter
        """

        lint = PyFlakesLinter
        PyFlakes(
            self.callback, self.uid, self.vid, lint, settings, code, filename)

    def pep8(self, settings, code, filename):
        """Run the pep8 linter
        """

        lint = Pep8Linter
        PEP8(self.callback, self.uid, self.vid, lint, settings, code, filename)

    def pep257(self, settings, code, filename):
        """Run the pep257 linter
        """

        lint = AnacondaPep257
        ignore = settings.get('pep257_ignore')
        PEP257(self.callback, self.uid, self.vid, lint, ignore, code, filename)

    def pylint(self, settings, code, filename):
        """Run the pyling linter
        """

        if not PYLINT_AVAILABLE:
            errors = 'Your configured python interpreter can\'t import pylint'
            self._failures.append({
                'success': False,
                'errors': errors,
                'uid': self.uid,
                'vid': self.vid
            })
            return

        rcfile = settings.get('pylint_rcfile', False)
        PyLint(self.callback, self.uid, self.vid, PyLinter, rcfile, filename)

    def _configure_linters(self, settings):
        """Enable or disable linters
        """

        self._linters['pyflakes'] = settings.get('use_pyflakes', True)
        self._linters['pylint'] = settings.get('use_pylint', False)
        self._linters['pep257'] = settings.get('use_pep257', False)
        self._linters['pep8'] = settings.get('pep8', True)

    def _merge_results(self, lint_result):
        """Merge the given linter results
        """

        if lint_result['success'] is True:
            self._errors.extend(lint_result)
        else:
            self._failures.extend(lint_result)
