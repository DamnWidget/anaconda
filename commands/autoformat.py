
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

import sublime
import sublime_plugin

from ..anaconda_lib import autopep
from ..anaconda_lib.decorators import is_python
from ..anaconda_lib.helpers import get_settings
from ..anaconda_lib.progress_bar import ProgressBar


class AnacondaAutoFormat(sublime_plugin.TextCommand):

    """Execute autopep8 formating
    """

    data = None

    def run(self, edit):
        if self.data is not None:
            self.replace(edit)
            return

        aggresive_level = get_settings(self.view, 'aggressive', 0)
        if aggresive_level > 0:
            if not sublime.ok_cancel_dialog(
                'You have an aggressive level of {} this may cause '
                'anaconda to change things that you don\'t really want to '
                'change.\n\nAre you sure do you want to continue?'.format(
                    aggresive_level
                )
            ):
                return

        self.code = self.view.substr(sublime.Region(0, self.view.size()))
        settings = {
            'aggressive': aggresive_level,
            'list-fixes': get_settings(self.view, 'list-fixes', False),
            'autoformat_ignore': get_settings(
                self.view, 'autoformat_ignore', []
            ),
            'autoformat_select': get_settings(
                self.view, 'autoformat_select', []
            ),
            'pep8_max_line_length': get_settings(
                self.view, 'pep8_max_line_length', 79
            )
        }
        try:
            messages = {
                'start': 'Autoformatting please wait...',
                'end': 'Autoformatting done!'
            }
            self.pbar = ProgressBar(messages)
            self.pbar.start()
            self.view.set_read_only(True)

            autopep.AnacondaAutopep8(
                settings, self.code, self.get_data).start()

        except:
            logging.error(traceback.format_exc())

    def is_enabled(self):
        """Determine if this command is enabled or not
        """

        return is_python(self.view, True)

    def get_data(self, data):
        """Collect the returned data from autopep8
        """

        self.data = data
        self.pbar.terminate()
        self.view.set_read_only(False)
        self.view.run_command('anaconda_auto_format')

    def replace(self, edit):
        """Replace the old code with what autopep8 gave to us
        """

        if self.code != self.data:
            region = sublime.Region(0, self.view.size())
            self.view.replace(edit, region, self.data)

        self.code = None
        self.data = None
