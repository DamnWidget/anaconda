
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import time

import sublime
import sublime_plugin

from ..anaconda_lib.decorators import (
    only_python, not_scratch, on_linting_enabled, on_linting_behaviour
)
from ..anaconda_lib.linting.sublime import (
    ANACONDA, erase_lint_marks, toggle_linting_behaviour, run_linter,
    last_selected_lineno, update_statusbar
)


class BackgroundLinter(sublime_plugin.EventListener):
    """Background linter, can be turned off via plugin settings
    """

    def __init__(self):
        super(BackgroundLinter, self).__init__()
        self.last_selected_line = -1
        s = sublime.load_settings('Anaconda.sublime-settings')
        s.add_on_change(
            'anaconda_linting_behaviour',  toggle_linting_behaviour
        )

    @only_python
    @not_scratch
    @on_linting_enabled
    @on_linting_behaviour(['always'])
    def on_modified_async(self, view):
        """
        Called after changes have been made to a view.
        Runs in a separate thread, and does not block the application.
        """

        # update the last selected line number
        self.last_selected_line = -1
        ANACONDA['LAST_PULSE'] = time.time()
        ANACONDA['ALREADY_LINTED'] = False
        erase_lint_marks(view)

    @only_python
    @on_linting_enabled
    @on_linting_behaviour(['always', 'load-save'])
    def on_load(self, view):
        """Called after load a file
        """

        if 'Python' in view.settings().get('syntax'):
            run_linter(view)

    @only_python
    @not_scratch
    @on_linting_enabled
    def on_post_save_async(self, view):
        """Called post file save event
        """

        run_linter(view)

    @only_python
    @on_linting_enabled
    @on_linting_behaviour(['always', 'load-save'])
    def on_activated_async(self, view):
        """Called when a view gain the focus
        """

        if 'Python' in view.settings().get('syntax'):
            run_linter(view)

    @only_python
    @not_scratch
    @on_linting_enabled
    def on_selection_modified_async(self, view):
        """Called on selection modified
        """

        if not 'Python' in view.settings().get('syntax'):
            return

        last_selected_line = last_selected_lineno(view)

        if last_selected_line != self.last_selected_line:
            self.last_selected_line = last_selected_line
            update_statusbar(view)

    def _erase_marks(self, view):
        """Just a wrapper for erase_lint_marks
        """

        erase_lint_marks(view)
