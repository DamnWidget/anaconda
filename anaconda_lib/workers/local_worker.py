
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import time

import sublime

from ..logger import Log
from .worker import Worker
from ..helpers import project_name
from ..constants import WorkerStatus
from ..builder.python_builder import AnacondaSetPythonBuilder


class LocalWorker(Worker):
    """This class implements a local worker that uses a local jsonserver
    """

    def __init__(self, interpreter):
        self.reconnecting = False
        super(LocalWorker, self).__init__(interpreter)

    def check(self):
        """Perform required checks to conclude if it is safe to operate
        """

        if not self.process.healthy:
            self.error = self.process.error
            self.tip = self.process.tip
            return False

        start = time.time()
        while not self._status(0.05):
            if time.time() - start >= 1:  # 1s
                return False
            time.sleep(0.1)

        return True

    def start(self):
        """Start the worker
        """

        self._update_python_builder()
        if self.reconnecting:
            self.interpreter.renew_interpreter()

        super(LocalWorker, self).start()

    def stop(self):
        """Stop it now please
        """

        self.process.stop()
        self.client.close()
        self.status = WorkerStatus.incomplete

    def on_python_interpreter_switch(self, raw_python_interpreter):
        """This method is called when there is a python interpreter switch
        """

        switch = False
        if self.interpreter.project_name is not None:
            if project_name() != self.interpreter.project_name:
                switch = True

            if self.process._process.args[0] != raw_python_interpreter:
                switch = True

        if switch:
            # check if our interpreter is not local anymore
            self.renew_interpreter(raw_python_interpreter)
            if not self.interpreter.for_local:
                # just fire this worker, it's not useful anymore
                Log.info('Firing worker {}...'.format(self))
                self.stop()
                self.status = WorkerStatus.quiting
                return

            self.reconnecting = True
            self.stop()

    def _update_python_builder(self):
        """Update the python builder in the config file
        """

        p_data = sublime.active_window().project_data()
        if p_data is not None:
            AnacondaSetPythonBuilder().update_interpreter_build_system(
                self.interpreter.python
            )

    def _status(self, timeout=0.05):
        """Check the socket status, returns True if it is operable
        """

        self.tip = (
            'check that there is Python process executing the anaconda '
            'jsonserver.py script running in your system. If there is, check '
            'that you can connect to your localhost writing the following '
            'script in your Sublime Text 3 console:\n\n'
            'import socket;socket.socket(socket.AF_INET, socket.SOCK_STTREAM).'
            'connect(("localhost", {}))\n\n'
            'Note: the port is the first number of the Python process '
            'that you found earlier'.format(self.interpreter.port)
        )
        return super(LocalWorker, self)._status(timeout)
