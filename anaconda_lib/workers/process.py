
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from .local_process import LocalProcess
from .remote_process import StubProcess
from .vagrant_process import VagrantProcess


class WorkerProcess(object):
    """Return a right processer based in the scheme
    """

    _processers = {'tcp': StubProcess, 'vagrant': VagrantProcess}

    def __init__(self, interpreter):
        self._interpreter = interpreter

    def take(self):
        scheme = self._interpreter.scheme
        return self._processers.get(scheme, LocalProcess)(self._interpreter)
