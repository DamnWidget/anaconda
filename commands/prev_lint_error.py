
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib.helpers import get_settings
from ..anaconda_lib.helpers import valid_languages
from ..anaconda_lib.linting.sublime import ANACONDA, update_statusbar


class AnacondaPrevLintError(sublime_plugin.WindowCommand):
    """Jump to the previous lint error on the page
    """

    def run(self) -> None:
        self.jump(self._harvest_prev())
        update_statusbar(self.window.active_view())

    def is_enabled(self) -> bool:
        """Determines if the command is enabled
        """

        view = self.window.active_view()
        if (view.file_name() in ANACONDA['DISABLED']
                or not get_settings(view, 'anaconda_linting')):
            return False

        location = view.sel()[0].begin()
        for lang in valid_languages():
            matcher = 'source.{}'.format(lang)
            if view.match_selector(location, matcher) is True:
                return True

        return False

    def jump(self, lineno: int = None) -> None:
        """Jump to a line in the view buffer
        """

        if lineno is None:
            sublime.status_message('No lint errors')
            return

        pt = self.window.active_view().text_point(lineno, 0)
        self.window.active_view().sel().clear()
        self.window.active_view().sel().add(sublime.Region(pt))

        self.window.active_view().show_at_center(pt)

    def _harvest_prev(self) -> int:
        """Harvest the prev error that we find and return it back
        """

        (cur_line, cur_col) = self.window.active_view().rowcol(
            self.window.active_view().sel()[0].begin()
        )
        lines = set([])
        vid = self.window.active_view().id()
        for error_type in ['ERRORS', 'WARNINGS', 'VIOLATIONS']:
            for line, _ in ANACONDA[error_type].get(vid, {}).items():
                lines.add(int(line))

        lines = sorted(lines)
        if not len(lines):
            return None

        if cur_line is not None and lines[0] < cur_line:
            lines = [l for l in lines if l < cur_line]

        return lines[-1] if len(lines) > 0 else None
