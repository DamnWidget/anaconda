#!/usr/bin/env python

"""
Start the anaconda standalone server in the background with the
configuration stored in config.py
"""

from __future__ import print_function

import os
import sys
import time

import config
from anaconda_lib.helpers import create_subprocess, get_traceback


interpreter = config.python_interpreter

args = []
args.append(interpreter if interpreter is not None else 'python')
args.append(os.path.join(
    os.path.dirname(__file__),
    '../anaconda_server/jsonserver.py')
)
args.append('-p')
args.append(config.project if config.project is not None else 'anaconda')
if config.extra_paths is not None:
    args.append('-e')
    args.append(','.join(config.extra_paths))
args.append(config.port if config.port is not None else 19360)

print('Starting the server...'.ljust(73), end='')
try:
    proc = create_subprocess(args)

    time.sleep(3.0)
    if proc.poll() is None:
        print('[Ok]')
        sys.exit(0)
    else:
        print('[Fail]')
        print(proc.communicate())
        sys.exit(-1)
except Exception as error:
    print('[Fail]')
    print(error)
    print(get_traceback())
    sys.exit(-1)
