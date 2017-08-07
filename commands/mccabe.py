
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib._typing import Dict, Any
from ..anaconda_lib.callback import Callback
from ..anaconda_lib.helpers import get_settings


class AnacondaMcCabe(sublime_plugin.WindowCommand):
    """Execute McCabe complexity checker
    """

    def run(self) -> None:

        view = self.window.active_view()
        code = view.substr(sublime.Region(0, view.size()))
        data = {
            'code': code,
            'threshold': get_settings(view, 'mccabe_threshold', 7),
            'filename': view.file_name(),
            'method': 'mccabe',
            'handler': 'qa'
        }
        Worker().execute(Callback(on_success=self.prepare_data), **data)

    def is_enabled(self) -> bool:
        """Determine if this command is enabled or not
        """

        view = self.window.active_view()
        location = view.sel()[0].begin()
        matcher = 'source.python'
        return view.match_selector(location, matcher)

    def prepare_data(self, data: Dict[str, Any]) -> None:
        """Prepare the data to present in the quick panel
        """

        if not data['success'] or data['errors'] is None:
            sublime.status_message('Unable to run McCabe checker...')
            return

        if len(data['errors']) == 0:
            view = self.window.active_view()
            threshold = get_settings(view, 'mccabe_threshold', 7)
            sublime.status_message(
                'No code complexity beyond {} was found'.format(threshold)
            )

        self._show_options(data['errors'])

    def _show_options(self, options: Dict[str, Any]) -> None:
        """Show a dropdown quickpanel with options to jump
        """

        self.options = []  # type: List[List[str]]
        for option in options:
            self.options.append(
                [option['message'], 'line: {}'.format(option['line'])]
            )

        self.window.show_quick_panel(self.options, self._jump)

    def _jump(self, item: int) -> None:
        """Jump to a line in the view buffer
        """

        if item == -1:
            return

        lineno = int(self.options[item][1].split(':')[1].strip()) - 1
        pt = self.window.active_view().text_point(lineno, 0)
        self.window.active_view().sel().clear()
        self.window.active_view().sel().add(sublime.Region(pt))

        self.window.active_view().show(pt)
