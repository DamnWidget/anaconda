# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda helpers
"""

import os
import traceback
import subprocess


def create_subprocess(args, **kwargs):
    """Create a subprocess and return it back
    """

    if not 'cwd' in kwargs:
        kwargs['cwd'] = os.path.dirname(os.path.abspath(__file__))
    kwargs['bufsize'] = -1

    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs['startupinfo'] = startupinfo

    return subprocess.Popen(args, **kwargs)

def get_traceback():
    """Get traceback log
    """

    traceback_log = []
    for traceback_line in traceback.format_exc().splitlines():
        traceback_log.append(traceback_line)

    return '\n'.join(traceback_log)
