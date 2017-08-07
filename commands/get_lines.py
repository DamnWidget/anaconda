
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib._typing import Dict, Any
from ..anaconda_lib.helpers import get_settings
from ..anaconda_lib.helpers import valid_languages
from ..anaconda_lib.linting.sublime import ANACONDA


class AnacondaGetLines(sublime_plugin.WindowCommand):
    """Get a quickpanel with all the errors and lines ready to jump to them
    """

    def run(self) -> None:
        errors = {}  # type: Dict[int, str]
        self._harvest_errors(errors, 'ERRORS')
        self._harvest_errors(errors, 'WARNINGS')
        self._harvest_errors(errors, 'VIOLATIONS')

        if len(errors) > 0:
            self.options = []  # type: List[List[str]]
            for line, error_strings in errors.items():

                for msg in error_strings:
                    self.options.append([msg, 'line: {}'.format(line)])

            self.window.show_quick_panel(self.options, self._jump)

    def is_enabled(self) -> bool:
        """Determines if the command is enabled
        """

        view = self.window.active_view()
        if (view.file_name() in ANACONDA['DISABLED'] or
                not get_settings(view, 'anaconda_linting')):
            return False

        location = view.sel()[0].begin()
        for lang in valid_languages():
            matcher = 'source.{}'.format(lang)
            if view.match_selector(location, matcher) is True:
                return True

        return False

    def _harvest_errors(self, harvester: Dict[str, Any], error_type: str) -> None:  # noqa
        vid = self.window.active_view().id()
        for line, error_strings in ANACONDA[error_type].get(vid, {}).items():
            if line not in harvester:
                harvester[line] = []

            for error in error_strings:
                harvester[line].append(error)

    def _jump(self, item: int) -> None:
        """Jump to a line in the view buffer
        """

        if item == -1:
            return

        lineno = int(self.options[item][1].split(':')[1].strip())
        pt = self.window.active_view().text_point(lineno, 0)
        self.window.active_view().sel().clear()
        self.window.active_view().sel().add(sublime.Region(pt))

        self.window.active_view().show(pt)
