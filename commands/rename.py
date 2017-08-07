# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import time
import logging
import traceback

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib._typing import Dict, Any
from ..anaconda_lib.callback import Callback
from ..anaconda_lib.helpers import prepare_send_data, is_python


class AnacondaRename(sublime_plugin.TextCommand):
    """Rename the word under the cursor to the given one in its total scope
    """

    data = None  # type: Dict[str, Any]

    def run(self, edit: sublime.Edit) -> None:
        if self.data is None:
            try:
                location = self.view.word(self.view.sel()[0].begin())
                old_name = self.view.substr(location)
                sublime.active_window().show_input_panel(
                    "Replace with:", old_name, self.input_replacement,
                    None, None
                )
            except Exception:
                logging.error(traceback.format_exc())
        else:
            self.rename(edit)

    def is_enabled(self) -> bool:
        """Determine if this command is enabled or not
        """

        return is_python(self.view)

    def input_replacement(self, replacement: str) -> None:
        location = self.view.rowcol(self.view.sel()[0].begin())
        data = prepare_send_data(location, 'rename', 'jedi')
        data['directories'] = sublime.active_window().folders()
        data['new_word'] = replacement
        Worker().execute(Callback(on_success=self.store_data), **data)

    def store_data(self, data: Dict[str, Any]) -> None:
        """Just store the data an call the command again
        """

        self.data = data
        self.view.run_command('anaconda_rename')

    def rename(self, edit: sublime.Edit) -> None:
        """Rename in the buffer
        """

        data = self.data
        if data['success'] is True:
            for filename, data in data['renames'].items():
                for line in data:
                    view = sublime.active_window().open_file(
                        '{}:{}:0'.format(filename, line['lineno']),
                        sublime.ENCODED_POSITION
                    )
                    while view.is_loading():
                        time.sleep(0.01)

                    lines = view.lines(sublime.Region(0, view.size()))
                    view.replace(edit, lines[line['lineno']], line['line'])

        self.data = None
