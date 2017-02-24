
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
MYPY_VERSION = None
try:
    from mypy import main as mypy
    MYPY_SUPPORTED = True
    MYPY_VERSION = tuple(
      int(i) for i in mypy.__version__.replace('-dev', '').split('.')
    )
    del mypy
except ImportError:
    print('MyPy is enabled but we could not import it')
    logging.info('MyPy is enabled but we could not import it')
    pass


class MyPy(object):
    """MyPy class for Anaconda
    """

    def __init__(self, code, filename, mypypath, settings):
        self.code = code
        self.filename = filename
        self.mypypath = mypypath
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

        err_ctx = '--hide-error-context'
        if MYPY_VERSION < (0, 4, 5):
            err_ctx = '--suppress-error-context'

        args = shlex.split('\'{0}\' -O -m mypy {1} {2} \'{3}\''.format(
            sys.executable, err_ctx,
            ' '.join(self.settings[:-1]), self.filename)
        )
        env = os.environ.copy()
        if self.mypypath is not None and self.mypypath != "":
            env['MYPYPATH'] = self.mypypath

        kwargs = {
            'cwd': os.path.dirname(os.path.abspath(__file__)),
            'bufsize': -1,
            'env': env
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

            data = line.split(':') if os.name != 'nt' else line[2:].split(':')
            errors.append({
                'level': 'W',
                'lineno': int(data[1]),
                'offset': 0,
                'code': ' ',
                'raw_error': '[W] MyPy {0}: {1}'.format(
                    data[2], data[3]
                ),
                'message': '[W] MyPy%s: %s',
                'underline_range': True
            })

        return errors
