
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import time

import sublime

from .worker import Worker
from ..helpers import project_name
from ..constants import WorkerStatus
from ..progress_bar import ProgressBar
from ..vagrant import VagrantMachineGlobalInfo, VagrantStartMachine


class VagrantWorker(Worker):
    """
    This class implements a local worker that uses a instance of anaconda
    minserver in a local vagrant guest VM
    """

    def __init__(self, interpreter):
        super(VagrantWorker, self).__init__(interpreter)

    def start(self):
        """Start the vagrant worker
        """

        if not self.check_config():
            return False

        return super(VagrantWorker, self).start()

    def check_config(self):
        """Check the configuration looks fine
        """

        if self.interpreter.network is None:
            self.interpreter.network = 'forwarded'

        network = self.interpreter.network
        if network == 'public' and self.interpreter.dev is None:
            self.error = (
                'network is configured as public but no device is specified'
            )
            self.tip = (
                'Specify a network device using `dev=<net_iface> or '
                'use a different network topology'
            )
            return False

        if network == 'private' and self.interpreter.address is None:
            self.error = (
                'vagrant network configured as private but '
                'no address has been supplied'
            )
            self.tip = (
                'Add the address parameter to your vagrant URI or change the '
                'network parameter to forwarded'
            )
            return False

        if not self._check_status():

            self.error = 'vagrant machine {} is not running'.format(
                self.interpreter.machine)
            self.tip = 'Start the vagrant machine'

            start_now = sublime.ok_cancel_dialog(
                '{} virtual machine is not running, do you want to start it '
                'now (it may take a while)?'.format(
                    self.interpreter.machine), 'Start Now'
            )
            if start_now:
                sublime.active_window().run_command(
                    'show_panel', {'panel': 'console', 'toggle': False})
                try:
                    messages = {
                        'start': 'Starting {} VM, please wait...'.format(
                            self.interpreter.machine
                        ),
                        'end': 'Done!',
                        'fail': 'Machine {} could not be started'.format(
                            self.interpreter.machine
                        ), 'timeout': ''
                    }
                    pbar = ProgressBar(messages)
                    VagrantStartMachine(
                        self.interpreter.machine, self.interpreter.vagrant_root
                    )
                except RuntimeError as error:
                    pbar.terminate(status=pbar.Status.FAILURE)
                    sublime.error_message(str(error))
                    return False
                else:
                    pbar.terminate()
                    sublime.message_dialog('Machine {} started.'.format(
                        self.interpreter.machine
                    ))
                    return self.check()

            return False

        return True

    def check(self):
        """Perform required checks to conclude if it's safe to operate
        """

        if self.interpreter.manual is None:
            if not self.process.healthy:
                self.error = self.process.error
                self.tip = self.process.tip
                return False

        start = time.time()
        while not self._status():
            if time.time() - start >= 2:  # 2s
                self.error = "can't connect to the minserver on {}:{}".format(
                    self.interpreter.host, self.interpreter.port
                )
                self.tip = 'check your vagrant machine is running'
                return False
            time.sleep(0.1)

        return True

    def stop(self):
        """Stop it now please
        """

        self.process.stop()
        self.client.close()
        self.status = WorkerStatus.incomplete

    def on_python_interpreter_switch(self, raw_python_interpreter):
        """This method is called when there is a python interpreter change
        """

        switch = False
        if self.interpreter.project_name is not None:
            if project_name() != self.interpreter.project_name:
                switch = True

            if self.interpreter.raw_interpreter != raw_python_interpreter:
                switch = True

        if switch:
            # check if our interpreter is not local anymore
            self.renew_interpreter(raw_python_interpreter)
            if not self.interpreter.for_vagrant:
                # just fire this worker, it's not useful anymore
                self.stop()
                self.status = WorkerStatus.quiting
                return

            self.reconnecting = True
            self.stop()

    def _check_status(self):
        """Check vagrant statsu and translate machine ID
        """

        try:
            vagrant_info = VagrantMachineGlobalInfo(self.interpreter.machine)
        except RuntimeError as error:
            self.errr = error
            self.tip = 'Install vagrant or add it to your path'
            return False

        if not vagrant_info.machine_id:
            self.error = 'Vagrant machine {} does not exists'.format(
                vagrant_info.machine
            )
            self.tip = 'Create and start your Vagrant machine'
            return False

        self.interpreter.machine_id = vagrant_info.machine_id
        self.interpreter.vagrant_root = vagrant_info.directory
        return vagrant_info.status == 'running'

    def _status(self, timeout=0.5):
        """Check the socket status, return True e if is operable
        """

        self.tip = (
            'check that your vagrant machine is running and the minserver'
            'is being executed in the guest {} port {}'.format(
                self.interpreter.machine, self.interpreter.port
            )
        )
        return super(VagrantWorker, self)._status(timeout)
