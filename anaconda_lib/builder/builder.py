
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details


import os
import threading

from ..helpers import create_subprocess, PIPE


class AnacondaBuilder(threading.Thread):
    """Base class for all anaconda builders
    """

    _daemon_wrapper = '{}/builder_daemon.py'.format(
        os.path.dirname(os.path.abspath(__file__))
    )

    def __init__(self, callback, runner, *params):
        self.buffer = ""
        self.callback = callback
        self.runner = runner
        self.params = [AnacondaBuilder._daemon_wrapper, runner] + [params]
        self.proc = create_subprocess(
            self.params, stdout=PIPE, stderr=PIPE, cwd=os.getcwd()
        )

    def kill(self):
        """Kill the process and return back the satus
        """

        if self.proc.poll() is not None:
            self.proc.kill()
            return self.proc.communicate()
