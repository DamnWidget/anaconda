
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import platform

logpath = {
    'linux': os.path.join('~', '.local', 'share', 'anaconda', 'logs'),
    'darwin': os.path.join('~', 'Library', 'Logs', 'anaconda'),
    'windows': os.path.join(os.getenv('APPDATA') or '~', 'Anaconda', 'Logs')
}

log_directory = os.path.expanduser(
    logpath.get(platform.system().lower())
)
