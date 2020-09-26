
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib._typing import Dict, Any
from ..anaconda_lib.progress_bar import ProgressBar
from ..anaconda_lib.helpers import get_settings, is_python, get_window_view
from ..anaconda_lib.jsonclient import Callback


class AnacondaAutoFormat(sublime_plugin.TextCommand):
    """Execute autopep8 formating
    """

    data = None

    def run(self, edit: sublime.Edit) -> None:
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
            ),
            'tab_size': get_settings(self.view, 'tab_size', 4)
        }
        try:
            messages = {
                'start': 'Autoformatting.  Please wait... ',
                'end': 'Autoformatting done!',
                'fail': 'Autoformatting failed, buffer not changed.',
                'timeout': 'Autoformatting failed, buffer not changed.',
            }
            self.pbar = ProgressBar(messages)
            self.pbar.start()
            self.view.set_read_only(True)

            data = {
                'vid': self.view.id(),
                'code': self.code,
                'method': 'pep8',
                'settings': settings,
                'handler': 'autoformat'
            }
            timeout = get_settings(self.view, 'auto_formatting_timeout', 1)

            callback = Callback(timeout=timeout)
            callback.on(success=self.get_data)
            callback.on(error=self.on_failure)
            callback.on(timeout=self.on_failure)

            Worker().execute(callback, **data)
        except:
            logging.error(traceback.format_exc())

    def on_failure(self, *args: Any, **kwargs: Any) -> None:
        self.pbar.terminate(status=self.pbar.Status.FAILURE)
        self.view.set_read_only(False)

    def is_enabled(self) -> bool:
        """Determine if this command is enabled or not
        """

        return is_python(self.view, True)

    def get_data(self, data: Dict[str, Any]) -> None:
        """Collect the returned data from autopep8
        """

        self.data = data
        self.pbar.terminate()
        self.view.set_read_only(False)
        self.view.run_command('anaconda_auto_format')

    def replace(self, edit: sublime.Edit) -> None:
        """Replace the old code with what autopep8 gave to us
        """

        view = get_window_view(self.data['vid'])
        if self.code != self.data.get('buffer'):
            region = sublime.Region(0, view.size())
            view.replace(edit, region, self.data.get('buffer'))
            if get_settings(view, 'auto_formatting'):
                sublime.set_timeout(lambda: view.run_command("save"), 0)

        self.code = None
        self.data = None
