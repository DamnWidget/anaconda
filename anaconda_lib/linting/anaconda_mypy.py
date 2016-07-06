
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda MyPy wrapper
"""

import re
import sys

MYPY_SUPPORTED = False
try:
    from mypy import main as mypy
    MYPY_SUPPORTED = True
except ImportError:
    pass


class MyPy(object):
    """MyPy class for Anaconda
    """

    def __init__(self, code, filename, settings):
        self.code = code
        self.filename = filename
        self.settings = settings

    def execute(self):
        """Check the code with MyPy check types
        """

        if not MYPY_SUPPORTED:
            raise RuntimeError("MyPy was not found")

        errors = []
        try:
            exit = sys.exit
            sys.exit = lambda x: None
            errors = self.check_source()
            sys.exit = exit
        except Exception as error:
            print(error)

        return errors

    def check_source(self):
        """Wrap calls to MyPy as a library
        """

        errors = []
        sources, options = self._parse_options()
        result = mypy.type_check_only(sources, None, options)
        for error in result.manager.errors.error_info:
            errors.append({
                'level': 'W',
                'lineno': error.line,
                'offset': 0,
                'code': ' ',
                'raw_error': '[W] MyPy {0}: {1}'.format(
                    error.severity, error.message
                ),
                'message': '[W] MyPy%s: %s',
                'underline_range': True
            })

        return errors

    def _parse_options(self):
        """Parse options using mypy
        """

        self.settings.append(self.filename)

        # check MyPy version
        match = re.match(r'(\d).(\d).(\d)', mypy.__version__)
        if match is not None:
            mypy_version = tuple(int(i) for i in (
                match.group(1), match.group(2), match.group(3)))
        else:
            mypy_version = (0, 0, 0)

        if mypy_version >= (0, 4, 3):
            return mypy.process_options(self.settings)

        sys_argv = sys.argv
        sys.argv = [''] + self.settings
        sources, options = mypy.process_options()
        sys.argv = sys_argv
        return sources, options
