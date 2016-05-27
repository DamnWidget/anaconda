
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from ..logger import Log
from .worker import Worker
from ..helpers import project_name
from ..constants import WorkerStatus


class RemoteWorker(Worker):
    """This class implements a remote worker
    """

    def __init__(self, interpreter):
        self.reconnecting = False
        super(RemoteWorker, self).__init__(interpreter)

    def stop(self):
        """Stop it now please
        """

        self.client.close()
        self.status = WorkerStatus.incomplete

    def check(self):
        """Perform common checks
        """

        if self.interpreter.host is None or self.interpreter.port is None:
            self.error = 'Host and port must be configured'
            self.tip = 'Fix your `python_interpreter` configuration'
            return False

        return self._status()

    def on_python_interpreter_switch(self, raw_python_interpreter):
        """This method is called when there is a python interpreter change
        """

        def _fire_worker():
            # just fire this workewr, is not useful anymore
            self.stop()
            self.status = WorkerStatus.quiting
            Log.info('Firing worker {}...'.format(self))

        if self.interpreter.project_name is not None:
            if project_name() != self.interpreter.project_name:
                self.renew_interpreter(raw_python_interpreter)
                # check if our interpeeter is not remote anymore
                if not self.interpreter.for_remote:
                    _fire_worker()

                self.reconnecting = True
                self.stop()

        if self.interpreter.raw_interpreter != raw_python_interpreter:
            # check if our interpreter is not remote anymore
            self.renew_interpreter(raw_python_interpreter)
            if not self.interpreter.for_remote:
                return _fire_worker()

            self.reconnecting = True
            self.stop()

    def _status(self, timeout=2):
        """Check the socker status and returnn True if is operable
        """

        self.tip = (
            'check that your Internet is working, the remote host is '
            'available from your network and the minserver.py is '
            'running in the remote host on port {}'.format(
                self.interpreter.port
            )
        )
        return super(RemoteWorker, self)._status(timeout)
