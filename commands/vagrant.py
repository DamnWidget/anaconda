
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from functools import partial

import sublime
import sublime_plugin

from ..anaconda_lib import worker, vagrant
from ..anaconda_lib.decorators import on_vagrant_enabled


class AnacondaVagrantEnable(sublime_plugin.WindowCommand):
    """Enable Vagrant on this window/project
    """

    def run(self):
        vagrant_worker = worker.WORKERS.get(sublime.active_window().id())
        if vagrant_worker is not None:
            vagrant_worker.support = True


class AnacondaVagrantBase(object):
    """Base class for vagrant commands
    """

    data = None

    def print_status(self, edit):
        """Print the vagrant command output string into a Sublime Text panel
        """

        vagrant_panel = self.view.window().create_output_panel(
            'anaconda_vagrant'
        )

        vagrant_panel.set_read_only(False)
        region = sublime.Region(0, vagrant_panel.size())
        vagrant_panel.erase(edit, region)
        vagrant_panel.insert(edit, 0, self.data)
        self.data = None
        vagrant_panel.set_read_only(True)
        vagrant_panel.show(0)
        self.view.window().run_command(
            'show_panel', {'panel': 'output.anaconda_documentation'}
        )


class AnacondaVagrantStatus(sublime_plugin.TextCommand, AnacondaVagrantBase):
    """Check vagrant status for configured project
    """

    data = None

    @on_vagrant_enabled
    def run(self, edit):
        cfg = self.window.active_view().settings().get('vagrant_environment')
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

    def prepare_data(self, data):
        """Prepare the returned data
        """

        success, output = data
        self.data = output
        sublime.active_window().run_command('anaconda_vagrant_status')


class AnacondaVagrantInit(sublime_plugin.TextCommand, AnacondaVagrantBase):
    """Execute vagrant init with the given parameters
    """

    def run(self, edit):
        cfg = self.window.active_view().settings().get('vagrant_environment')
        if self.data is None:
            self.view.window().show_input_panel(
                'Directory to init on:', '',
                partial(self.input_directory, cfg), None, None
            )
        else:
            self.print_status(edit)

    def input_directory(self, cfg, directory):
        machine = cfg.get('machine', 'default')
        vagrant.VagrantInit(self.prepare_data, directory, machine)

    def prepare_data(self, data):
        """Prepare the returned data
        """

        success, out, error = data
        self.data = error if not success else out
        sublime.active_window().run_command('anaconda_vagrant_init')
