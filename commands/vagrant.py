
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from functools import partial

import sublime
import sublime_plugin

from ..anaconda_lib import worker, vagrant
from ..anaconda_lib._typing import Dict, Any


class AnacondaVagrantEnable(sublime_plugin.WindowCommand):
    """Enable Vagrant on this window/project
    """

    def run(self) -> None:
        vagrant_worker = worker.WORKERS.get(sublime.active_window().id())
        if vagrant_worker is not None:
            vagrant_worker.support = True


class AnacondaVagrantBase(object):
    """Base class for vagrant commands
    """

    data = None  # type: Dict[str, Any]

    def __init__(self):
        super(AnacondaVagrantBase, self).__init__()
        self.view = None  # type: sublime.View

    def print_status(self, edit: sublime.Edit) -> None:
        """Print the vagrant command output string into a Sublime Text panel
        """

        vagrant_panel = self.view.window().create_output_panel(
            'anaconda_vagrant'
        )

        vagrant_panel.set_read_only(False)
        region = sublime.Region(0, vagrant_panel.size())
        vagrant_panel.erase(edit, region)
        vagrant_panel.insert(edit, 0, self.data.decode('utf8'))
        self.data = None
        vagrant_panel.set_read_only(True)
        vagrant_panel.show(0)
        self.view.window().run_command(
            'show_panel', {'panel': 'output.anaconda_vagrant'}
        )

    def prepare_data(self, data: Dict[str, Any]) -> None:
        """Prepare the returned data and call the given command
        """

        success, out, error = data
        self.data = error if not success else out
        sublime.active_window().run_command(self._class_name_to_command())

    def _class_name_to_command(self):
        """Convert class name to command
        """

        command = []
        for i in range(len(self.__class__.__name__)):
            c = self.__class__.__name__[i]
            if i == 0:
                command.append(c.lower())
            elif i > 0 and c.isupper():
                command.append('_')
                command.append(c.lower())
            else:
                command.append(c)

        return ''.join(command)


class AnacondaVagrantStatus(sublime_plugin.TextCommand, AnacondaVagrantBase):
    """Check vagrant status for configured project
    """

    data = None  # type: Dict[str, Any]

    def run(self, edit: sublime.Edit) -> None:
        if self.view.settings().get('vagrant_environment') is None:
            return

        cfg = self.view.settings().get('vagrant_environment')
        if self.data is None:
            try:
                vagrant.VagrantStatus(
                    self.prepare_data,
                    cfg.get('directory', ''),
                    cfg.get('machine', 'default'), True
                )
            except Exception as error:
                print(error)
        else:
            self.print_status(edit)

    def prepare_data(self, data: Dict[str, Any]) -> None:
        """Prepare the returned data
        """

        success, output = data
        self.data = output
        sublime.active_window().run_command('anaconda_vagrant_status')


class AnacondaVagrantInit(sublime_plugin.TextCommand, AnacondaVagrantBase):
    """Execute vagrant init with the given parameters
    """

    def run(self, edit: sublime.Edit) -> None:
        cfg = self.view.settings().get('vagrant_environment')
        if self.data is None:
            self.view.window().show_input_panel(
                'Directory to init on:', '',
                partial(self.input_directory, cfg), None, None
            )
        else:
            self.print_status(edit)

    def input_directory(self, cfg: Dict[str, Any], directory: str) -> None:
        machine = cfg.get('machine', 'default')
        vagrant.VagrantInit(self.prepare_data, directory, machine)


class AnacondaVagrantUp(sublime_plugin.TextCommand, AnacondaVagrantBase):
    """Execute vagrant up command
    """

    def run(self, edit: sublime.Edit) -> None:
        if self.view.settings().get('vagrant_environment') is None:
            return

        cfg = self.view.settings().get('vagrant_environment')
        if self.data is None:
            try:
                machine = cfg.get('machine', 'default')
                vagrant.VagrantUp(self.prepare_data, cfg['directory'], machine)
            except Exception as error:
                print(error)
        else:
            self.print_status(edit)


class AnacondaVagrantReload(sublime_plugin.TextCommand, AnacondaVagrantBase):
    """Execute vagrant reload command
    """

    def run(self, edit: sublime.Edit) -> None:
        if self.view.settings().get('vagrant_environment') is None:
            return

        cfg = self.view.settings().get('vagrant_environment')
        if self.data is None:
            try:
                machine = cfg.get('machine', 'default')
                vagrant.VagrantReload(
                    self.prepare_data, cfg['directory'], machine
                )
            except Exception as error:
                print(error)
        else:
            self.print_status(edit)


class AnacondaVagrantSsh(sublime_plugin.TextCommand, AnacondaVagrantBase):
    """Execute remmote ssh command
    """

    def run(self, edit: sublime.Edit) -> None:
        if self.view.settings().get('vagrant_environment') is None:
            return

        cfg = self.view.settings().get('vagrant_environment')
        if self.data is None:
            self.view.window().show_input_panel(
                'Command to execute:', '',
                partial(self.input_command, cfg), None, None
            )
        else:
            self.print_status(edit)

    def input_command(self, cfg: Dict[str, Any], command: str) -> None:
        machine = cfg.get('machine', 'default')
        vagrant.VagrantSSH(
            self.prepare_data, cfg['directory'], command, machine
        )
