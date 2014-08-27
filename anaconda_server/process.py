
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import logging
import subprocess


def spawn(args, **kwargs):
    """Spawn a subprocess and return it back
    """

    if not 'cwd' in kwargs:
        kwargs['cwd'] = os.path.dirname(os.path.abspath(__file__))
    kwargs['bufsize'] = -1

    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs['startupinfo'] = startupinfo

    try:
        return subprocess.Popen(args, **kwargs)
    except:
        logging.error(
            'Your operating system denied the spawn of {} process'.format(
                args[0])
        )
