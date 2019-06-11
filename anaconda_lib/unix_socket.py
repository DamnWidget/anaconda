
# Copyright (C) 2013 ~ 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software se LICENSE file for details

import os
import platform
import tempfile


class UnixSocketPath(object):
    """Encapsulate logic to handle with paths to UNIX domain sockets
    """

    socketpath = {
        'linux': os.path.join('~', '.local', 'share', 'anaconda', 'run'),
        'darwin': os.path.join(
            '~', 'Library', 'Application Support', 'Anaconda')
    }

    def __init__(self, project):
        self.__project = project
        self.__socket_file = os.path.join(
            os.path.expanduser(
                UnixSocketPath.socketpath.get(platform.system().lower())
            ),
            project or 'anaconda',
            'anaconda.sock'
        )

    @property
    def socket(self):
        """Return back a valid socket path always
        """

        if len(self.__socket_file) < 103:
            return self.__socket_file

        socket_path = os.path.join(
            tempfile.gettempdir(),
            self.__project or 'anaconda',
            'anaconda.sock'
        )
        if len(socket_path) > 103:
            # probably the project name is crazy long
            socket_path = os.path.join(
                tempfile.gettempdir(), self.__project[:10], 'anaconda.sock'
            )

        return socket_path


def get_current_umask():
    'Return the current umask without changing it.'
    current_umask = os.umask(0)
    os.umask(current_umask)
    return current_umask
