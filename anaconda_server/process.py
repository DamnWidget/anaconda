
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import logging
import subprocess


def spawn(args, **kwargs):
    """Spawn a subprocess and return it back
    """

    if 'cwd' not in kwargs:
        kwargs['cwd'] = os.path.dirname(os.path.abspath(__file__))
    kwargs['bufsize'] = -1

    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs['startupinfo'] = startupinfo

    try:
        return subprocess.Popen(args, **kwargs)
    except Exception as error:
        msg = (
            'Your operating system denied the spawn of {0} process: {1}'
        ).format(args[0], error)
        logging.error(msg)
        raise RuntimeError(msg)
