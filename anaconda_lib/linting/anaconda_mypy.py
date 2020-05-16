
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


def parse_mypy_version():
    try:
        from mypy import main as mypy
        version = mypy.__version__
        if "dev" in version:
            # Handle when Mypy is installed directly from github:
            # eg: 0.730+dev.ddec163790d107f1fd9982f19cbfa0b6966c2eea
            version = version.split("+dev.")[0]
            # Handle old style Mypy version: 0.480-dev
            version = version.replace('-dev', '')

        tuple_version = tuple(int(i) for i in version.split('.'))
        while len(tuple_version) < 3:
            tuple_version += (0,)
        return tuple_version
    except ImportError:
        print('MyPy is enabled but we could not import it')
        logging.info('MyPy is enabled but we could not import it')
        return None


class MyPy(object):
    """MyPy class for Anaconda
    """
    VERSION = parse_mypy_version()

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

        if MyPy.VERSION is None:
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

        err_sum = '--no-error-summary'
        if MyPy.VERSION < (0, 761, 0):
            err_sum = ''

        err_ctx = '--hide-error-context'
        if MyPy.VERSION < (0, 4, 5):
            err_ctx = '--suppress-error-context'

        dont_follow_imports = "--follow-imports silent"

        args = shlex.split('\'{0}\' -O -m mypy {1} {2} {3} {4} \'{5}\''.format(
            sys.executable, err_sum, err_ctx, dont_follow_imports,
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

            data = line.split(
                ':', maxsplit=3
            ) if os.name != 'nt' else line[2:].split(':', maxsplit=3)

            errors.append({
                'level': 'W',
                'lineno': int(data[1]),
                'offset': 0,
                'code': ' ',
                'raw_error': '[W] MyPy {0}: {1}'.format(
                    data[2].strip(), data[3].strip()
                ),
                'message': '[W] MyPy%s: %s',
                'underline_range': True
            })

        return errors
