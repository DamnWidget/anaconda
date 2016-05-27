
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import threading
import subprocess

from .logger import Log
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


class VagrantReload(VagrantBase):
    """Reload a vagrant box
    """

    def __init__(self, callback, vagrant_root, machine=None):
        super(VagrantReload, self).__init__(callback, vagrant_root, machine)
        self.start()

    def run(self):
        """Reload the vagrant box machine
        """

        self.wait_answer(['vagrant', 'reload', self.machine])


class VagrantStatus(VagrantBase):
    """Check vagrant box status
    """

    def __init__(self, callback, vagrant_root, machine=None, full=False):
        super(VagrantStatus, self).__init__(callback, vagrant_root, machine)
        self.full = full
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
            running = b'running' in output
            self.callback((True, running if not self.full else output))


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

        self.wait_answer(['vagrant', 'ssh', self.machine, '-c', self.cmd])


class VagrantIPAddress(object):
    """Get back the remote guest IP address in synchronous way
    """

    def __init__(self, root, machine=None, iface='eth1'):

        with vagrant_root(root):
            cmd = (
                'python -c "import socket, fcntl, struct;'
                's = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);'
                'print(socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, '
                'struct.pack(b\'256s\', b\'{}\'))[20:24]))"\n'
            ).format(iface)
            proc = create_subprocess(
                ['vagrant', 'ssh', machine, '-c', cmd],
                stdout=PIPE, stderr=PIPE, cwd=os.getcwd()
            )

        output, error = proc.communicate()
        if proc.poll() != 0:
            self.ip_address = None
        else:
            self.ip_address = output


class VagrantIPAddressGlobal(object):
    """Get back the remote guest IP address in synchronous way from global
    """

    def __init__(self, machine, iface='eth1'):

        cmd = (
            'python -c "import socket, fcntl, struct;'
            's = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);'
            'print(socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, '
            'struct.pack(b\'256s\', b\'{}\'))[20:24]))"\n'
        ).format(iface)
        proc = create_subprocess(
            ['vagrant', 'ssh', machine, '-c', cmd],
            stdout=PIPE, stderr=PIPE, cwd=os.getcwd()
        )

        output, error = proc.communicate()
        if proc.poll() != 0:
            self.ip_address = None
        else:
            self.ip_address = output


class VagrantMachineGlobalInfo(object):
    """Get vagrant machine information looking up in global stats
    """

    def __init__(self, machine):
        self.machine = machine
        self.status = ''
        self.machine_id = ''

        args = ('vagrant', 'global-status')
        p = create_subprocess(args, stdout=PIPE, stderr=PIPE)
        if p is None:
            raise RuntimeError('vagrant command not found')

        output, err = p.communicate()
        if err:
            raise RuntimeError(err)

        for line in output.splitlines()[2:]:
            if not line:
                continue

            if line.startswith(b'The'):
                break

            data = line.split()
            if not data:
                continue

            if data[1].decode('utf8') == machine:
                self.machine_id = data[0].decode('utf8')
                self.status = data[3].decode('utf8')
                self.directory = data[4].decode('utf8')
                break


class VagrantStartMachine(object):
    """Start a vagrant machine using it's global ID
    """

    def __init__(self, machine, directory):
        with vagrant_root(directory):
            args = ('vagrant', 'up', machine)
            p = create_subprocess(
                args, stdout=PIPE, stderr=PIPE, cwd=os.getcwd())
            if p is None:
                raise RuntimeError('vagrant command not found')

            output, err = p.communicate()
            Log.info(output.decode('utf8'))
            if err:
                # check if the machine is running using global stats
                info = VagrantMachineGlobalInfo(machine)
                if info.status != 'running':
                    raise RuntimeError(err)

                Log.error(err.decode('utf8'))
