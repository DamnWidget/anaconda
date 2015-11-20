
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.helpers import (
    prepare_send_data, get_settings, active_view, is_python,
    completion_is_disabled
)
from ..anaconda_lib.decorators import profile

JUST_COMPLETED = False


class AnacondaComletionEventListener(sublime_plugin.EventListener):
    """Anaconda completion events listener class
    """

    completions = []
    ready_from_defer = False

    @profile
    def on_query_completions(self, view, prefix, locations):
        """Sublime Text autocompletion event handler
        """

        if not is_python(view, autocomplete_ignore_repl=True):
            return

        if completion_is_disabled(view):
            return

        global JUST_COMPLETED

        if self.ready_from_defer is True:
            completion_flags = 0

            if get_settings(view, 'suppress_word_completions', False):
                completion_flags = sublime.INHIBIT_WORD_COMPLETIONS

            if get_settings(view, 'suppress_explicit_completions', False):
                completion_flags |= sublime.INHIBIT_EXPLICIT_COMPLETIONS

            cpl = self.completions
            self.completions = []
            self.ready_from_defer = False
            JUST_COMPLETED = True

            return (cpl, completion_flags)

        location = view.rowcol(locations[0])
        data = prepare_send_data(location, 'autocomplete', 'jedi')

        Worker().execute(self._complete, **data)

    def on_modified(self, view):
        """Called after changes has been made to a view.
        """

        if not is_python(view, autocomplete_ignore_repl=True):
            return

        global JUST_COMPLETED

        if (view.substr(view.sel()[0].begin() - 1) == '('
                and view.substr(view.sel()[0].begin()) == ')'):
            if JUST_COMPLETED:
                view.run_command('anaconda_complete_funcargs')

            JUST_COMPLETED = False
        elif view.substr(sublime.Region(
                view.sel()[0].begin() - 7, view.sel()[0].end())) == 'import ':
            self._run_auto_complete()

    def _complete(self, data):

        proposals = data['completions'] if data['success'] else []

        if proposals:
            active_view().run_command("hide_auto_complete")
            self.completions = proposals
            self.ready_from_defer = True

            # is the tab key is used to complete just undo the last insertion
            if active_view().command_history(0)[0] == 'insert_best_completion':
                if active_view().substr(sublime.Region(
                        active_view().sel()[0].begin() - 5,
                        active_view().sel()[0].end())) == 'self.':
                    active_view().run_command('undo')

            self._run_auto_complete()

    def _run_auto_complete(self):
        """Efectively call autocomplete using the ST API
        """

        active_view().run_command("auto_complete", {
            'disable_auto_insert': True,
            'api_completions_only': get_settings(
                active_view(), 'hide_snippets_on_completion', False),
            'next_completion_if_showing': False,
            'auto_complete_commit_on_tab': True,
        })
