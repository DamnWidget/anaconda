
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import shutil
import threading
import subprocess

from .contexts import vagrant_root
from .helpers import create_subprocess

PIPE = subprocess.PIPE


class VagrantBase(threading.Thread):
    """Spawn vagrant shell to execute commands (base class)
    """

    def __init__(self, callback, vagrant_root, machine):
        super(VagrantBase, self).__init__()
        self.machine = machine if machine is not None else 'default'
        self.callback = callback
        self.vagrant_root = vagrant_root

    def wait_answer(self, args):
        """Wait for an answer from the subprocess
        """

        with vagrant_root(self.vagrant_root):
            proc = create_subprocess(
                args, stdout=PIPE, stderr=PIPE, cwd=os.getcwd()
            )
            output, error = proc.communicate()

        self.callback((proc.poll() == 0, output, error))


class VagrantInit(VagrantBase):
    """Init a new vagrant environment with the given box
    """

    def __init__(self, callback, vagrant_root, box):
        super(VagrantInit, self).__init__(callback, vagrant_root)
        self.box = box
        self.start()

    def run(self):
        """Init the vagrant machine
        """

        self.wait_answer(['vagrant', 'init', self.box])


class VagrantUp(VagrantBase):
    """Start a vagrant box
    """

    def __init__(self, callback, vagrant_root, machine=None):
        super(VagrantUp, self).__init__(callback, vagrant_root, machine)
        self.start()

    def run(self):
        """Start the vagrant box machine
        """

        self.wait_answer(['vagrant', 'up', self.machine])


class VagrantStatus(VagrantBase):
    """Check vagrant box status
    """

    def __init__(self, callback, vagrant_root, machine=None):
        super(VagrantStatus, self).__init__(callback, vagrant_root, machine)
        self.start()

    def run(self):
        """Check the vagrant box machine status
        """

        args = ['vagrant', 'status', self.machine]
        with vagrant_root(self.vagrant_root):
            proc = create_subprocess(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
        output, error = proc.communicate()

        if proc.poll() != 0:
            self.callback((False, error))
        else:
            self.callback((True, b'running' in output))


class VagrantSSH(VagrantBase):
    """Execute a remote SSH command in a vagrant box
    """

    def __init__(self, callback, vagrant_root, cmd, machine=None):
        super(VagrantSSH, self).__init__(callback, vagrant_root, machine)
        self.cmd = cmd
        self.start()

    def run(self):
        """Execute a command through SSH in a vagrant box machine
        """

        print(self.cmd)
        self.wait_answer(['vagrant', 'ssh', self.machine, '-c', self.cmd])
