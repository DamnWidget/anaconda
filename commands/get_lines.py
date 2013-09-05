
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib.linting.sublime import ANACONDA


class AnacondaGetLines(sublime_plugin.WindowCommand):

    """Get a quickpanel with all the errors and lines ready to jump to them
    """

    def run(self):
        errors = {}
        self._harvest_errors(errors, 'ERRORS')
        self._harvest_errors(errors, 'WARNINGS')
        self._harvest_errors(errors, 'VIOLATIONS')

        if len(errors) > 0:
            self.options = []
            for line, error_strings in errors.items():

                for msg in error_strings:
                    self.options.append([msg, 'line: {}'.format(line)])

            self.window.show_quick_panel(self.options, self._jump)

    def is_enabled(self):
        """Determines if the command is enabled
        """

        view = self.window.active_view()
        if view.id() in ANACONDA['DISABLED']:
            return False

        location = view.sel()[0].begin()
        matcher = 'source.python'
        return view.match_selector(location, matcher)

    def _harvest_errors(self, harvester, error_type):
        vid = self.window.active_view().id()
        for line, error_strings in ANACONDA[error_type].get(vid, {}).items():
            if not line in harvester:
                harvester[line] = []

            for error in error_strings:
                harvester[line].append(error)

    def _jump(self, item):
        """Jump to a line in the view buffer
        """

        if item == -1:
            return

        lineno = int(self.options[item][1].split(':')[1].strip())
        pt = self.window.active_view().text_point(lineno, 0)
        self.window.active_view().sel().clear()
        self.window.active_view().sel().add(sublime.Region(pt))

        self.window.active_view().show(pt)
