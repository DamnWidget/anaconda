
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda MyPy wrapper
"""

import os
import sys
import shlex
import logging
import subprocess
from subprocess import PIPE, Popen


MYPY_SUPPORTED = False
try:
    from mypy import main as mypy
    MYPY_SUPPORTED = True
    del mypy
except ImportError:
    logging.info('MyPy is enabled but we could not import it')
    pass


class MyPy(object):
    """MyPy class for Anaconda
    """

    def __init__(self, code, filename, settings):
        self.code = code
        self.filename = filename
        self.settings = settings

    @property
    def silent(self):
        """Returns True if --silent-imports settig is present
        """

        return '--silent-imports' in self.settings

    def execute(self):
        """Check the code with MyPy check types
        """

        if not MYPY_SUPPORTED:
            raise RuntimeError("MyPy was not found")

        errors = []
        try:
            errors = self.check_source()
        except Exception as error:
            print(error)
            logging.error(error)

        return errors

    def check_source(self):
        """Wrap calls to MyPy as a library
        """

        args = shlex.split('{0} -O -m mypy {1} {2} {3}'.format(
            sys.executable, '--suppress-error-context',
            ' '.join(self.settings[:-1]), self.filename),
            posix=os.name != 'nt'
        )
        kwargs = {
            'cwd': os.path.dirname(os.path.abspath(__file__)),
            'bufsize': -1,
            'env': os.environ.copy()
        }
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kwargs['startupinfo'] = startupinfo

        proc = Popen(args, stdout=PIPE, stderr=PIPE, **kwargs)
        out, err = proc.communicate()
        if err is not None and len(err) > 0:
            if sys.version_info >= (3,):
                err = err.decode('utf8')
            raise RuntimeError(err)

        if sys.version_info >= (3,):
            out = out.decode('utf8')

        errors = []
        for line in out.splitlines():
            if (self.settings[-1] and not
                    self.silent and 'stub' in line.lower()):
                continue

            error_data = line.split(':')
            errors.append({
                'level': 'W',
                'lineno': int(error_data[1]),
                'offset': 0,
                'code': ' ',
                'raw_error': '[W] MyPy {0}: {1}'.format(
                    error_data[2], error_data[3]
                ),
                'message': '[W] MyPy%s: %s',
                'underline_range': True
            })

        return errors
