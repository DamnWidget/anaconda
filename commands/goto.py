
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.explore_panel import ExplorerPanel
from ..anaconda_lib.helpers import prepare_send_data, is_python


class AnacondaGoto(sublime_plugin.TextCommand):
    """Jedi GoTo a Python definition for Sublime Text
    """

    JEDI_COMMAND = 'goto'

    def run(self, edit: sublime.Edit) -> None:
        try:
            location = self.view.rowcol(self.view.sel()[0].begin())
            data = prepare_send_data(location, self.JEDI_COMMAND, 'jedi')
            Worker().execute(self.on_success, **data)
        except:
            pass

    def is_enabled(self) -> bool:
        """Determine if this command is enabled or not
        """

        return is_python(self.view)

    def on_success(self, data):
        """Called when a result comes from the query
        """

        if not data['result']:
            sublime.status_message('Could not find symbol')
            return

        symbols = []
        for result in data['result']:
            symbols.append({
                'title': result[0],
                'location': 'File: {} Line: {} Column: {}'.format(
                    result[1], result[2], result[3]
                ),
                'position': '{}:{}:{}'.format(result[1], result[2], result[3])
            })

        ExplorerPanel(self.view, symbols).show([])


class AnacondaGotoAssignment(AnacondaGoto):
    """Jedi GoTo a Python assignment for Sublime Text
    """
    JEDI_COMMAND = 'goto_assignment'


class AnacondaGotoPythonObject(sublime_plugin.TextCommand):
    """Open prompt asking for Python path and JediGoto
    """

    def input_package(self, package: str) -> None:
        splitted = package.strip().split('.')
        if len(splitted) == 1:
            import_command = 'import %s' % splitted[0]
        else:
            import_command = 'from %s import %s' % (
                '.'.join(splitted[:-1]), splitted[-1]
            )
        self.goto_python_object(import_command)

    def goto_python_object(self, import_command: str) -> None:
        try:
            data = {
                'filename': '',
                'method': 'goto',
                'line': 1,
                'offset': len(import_command),
                'source': import_command,
                'handler': 'jedi'
            }
            Worker().execute(self.on_success, **data)
        except:
            raise

    def run(self, edit: sublime.Edit) -> None:
        sublime.active_window().show_input_panel(
            'Provide object path:', '',
            self.input_package, None, None
        )

    def on_success(self, data):
        """Called when there is a response from the query
        """

        if not data['result']:
            sublime.status_message('Symbol not found...')
            return

        symbols = []
        for result in data['result']:
            symbols.append({
                'title': result[0],
                'location': 'File: {} Line: {} Column: {}'.format(
                    result[1], result[2], result[3]
                ),
                'position': '{}:{}:{}'.format(result[1], result[2], result[3])
            })

        ExplorerPanel(self.view, symbols).show([])
