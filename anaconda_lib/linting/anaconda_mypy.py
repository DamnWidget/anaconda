
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
    from mypy import api as mypyApi
    MYPY_SUPPORTED = True
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

        forced_args = ['--hide-error-context', '--show-traceback']
        all_args = self.settings + forced_args + [self.filename]

        if self.mypypath is not None and self.mypypath != "":
            os.environ['MYPYPATH'] = self.mypypath

        logging.info('calling mypy with %s' % str(all_args))

        (out, err, status) = mypyApi.run(all_args)
		
        if err is not None and len(err) > 0:
            raise RuntimeError(err)

        errors = []
        for line in out.splitlines():

            data = line.split(':') if os.name != 'nt' else line[2:].split(':')

            # mypy has paths relative to project, anaconda has paths absolute paths.
            # mypy returns errors that are not necessarily just for the current file.
            filename = data[0]
            if not self.filename.endswith(filename):
                continue

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
