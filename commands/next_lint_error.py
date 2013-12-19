
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib.helpers import get_settings
from ..anaconda_lib.linting.sublime import ANACONDA


class AnacondaNextLintError(sublime_plugin.WindowCommand):
    """Jump to the next lint error on the list
    """

    current_error = None

    def run(self):
        self.jump(self._harvest_first())

    def is_enabled(self):
        """Determines if the command is enabled
        """

        view = self.window.active_view()
        if (view.file_name() in ANACONDA['DISABLED']
                or not get_settings(view, 'anaconda_linting')):
            return False

        location = view.sel()[0].begin()
        matcher = 'source.python'
        return view.match_selector(location, matcher)

    def jump(self, lineno=None):
        """Jump to a line in the view buffer
        """

        if lineno is None:
            sublime.status_message('No lint errors')
            return

        pt = self.window.active_view().text_point(lineno, 0)
        self.window.active_view().sel().clear()
        self.window.active_view().sel().add(sublime.Region(pt))

        self.window.active_view().show(pt)

    def _harvest_first(self):
        """Harvest the first error that we find and return it back
        """

        vid = self.window.active_view().id()
        for error_type in ['ERRORS', 'WARNINGS', 'VIOLATIONS']:
            for line, _ in ANACONDA[error_type].get(vid, {}).items():
                return int(line)
