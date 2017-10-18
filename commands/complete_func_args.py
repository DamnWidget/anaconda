
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib._typing import Dict, Any
from ..anaconda_lib.callback import Callback
from ..anaconda_lib.helpers import (
    get_settings, active_view, prepare_send_data, is_python
)


class AnacondaCompleteFuncargs(sublime_plugin.TextCommand):
    """
    Function / Class constructor autocompletion command

    This is directly ported fronm SublimeJEDI
    """

    def run(self, edit: sublime.Edit, characters: str ='') -> None:
        if not get_settings(self.view, 'complete_parameters', False):
            return

        self._insert_characters(edit)

        location = active_view().rowcol(self.view.sel()[0].begin())
        data = prepare_send_data(location, 'parameters', 'jedi')
        data['settings'] = {
            'complete_parameters': get_settings(
                self.view, 'complete_parameters', False
            ),
            'complete_all_parameters': get_settings(
                self.view, 'complete_all_parameters', False
            )
        }
        callback = Callback(on_success=self.insert_snippet)
        Worker().execute(callback, **data)

    def is_enabled(self) -> bool:
        """Determine if this command is enabled or not
        """

        return is_python(self.view)

    def _insert_characters(self, edit: sublime.Edit) -> None:
        """
        Insert autocomplete character with closed pair
        and update selection regions

        :param edit: sublime.Edit
        :param characters: str
        """

        regions = [a for a in self.view.sel()]
        self.view.sel().clear()

        for region in reversed(regions):

            if self.view.settings().get('auto_match_enabled', True):
                position = region.end()
            else:
                position = region.begin()

            self.view.sel().add(sublime.Region(position, position))

    def insert_snippet(self, data: Dict[str, Any]) -> None:
        """Insert the snippet in the buffer
        """

        template = data['template']
        active_view().run_command('insert_snippet', {'contents': template})


class AnacondaFillFuncargs(sublime_plugin.TextCommand):
    """Trigger parameters autocompletion with key press."""

    def run(self, edit, all=False):

        req_args, all_args = 'complete_parameters', 'complete_all_parameters'
        compl_par = get_settings(self.view, req_args, False)
        compl_all = get_settings(self.view, all_args, False)

        # no need to do anything, just run the command
        if compl_all:
            self.view.run_command("anaconda_complete_funcargs")
            return

        # temporarily enable autocompletion
        if not compl_par:
            self.view.settings().set(req_args, True)
        if all:
            self.view.settings().set(all_args, True)

        self.view.run_command("anaconda_complete_funcargs")

        # restore value as per settings
        if not compl_par:
            self.view.settings().set(req_args, False)
        if all:
            self.view.settings().set(all_args, False)


class AnacondaFuncargsKeyListener(sublime_plugin.EventListener):
    """Allow parameters autocompletion with key press."""

    def on_query_context(self, view, key, operator, operand, match_all):

        if key == 'anaconda_insert_funcargs':

            def valid_scope():
                scope = view.scope_name(pos)
                if 'meta.function-call' in scope:
                    return True
                elif 'meta.function_call' in scope:
                    return True
                return False

            pos = view.sel()[0].a
            check = (view.substr(pos - 1) == '(' and view.substr(pos) == ')')
            allow = get_settings(
                view, 'parameters_completion_on_keypress', True)

            if allow and check and valid_scope():
                return True
        return None
