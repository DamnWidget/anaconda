
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.workers.market import Market
from ..anaconda_lib.helpers import is_remote_session
from ..anaconda_lib.explore_panel import ExplorerPanel
from ..anaconda_lib.helpers import prepare_send_data, is_python, get_settings


class AnacondaGoto(sublime_plugin.TextCommand):
    """Jedi GoTo a Python definition for Sublime Text
    """

    JEDI_COMMAND = 'goto'

    def run(self, edit: sublime.Edit) -> None:
        try:
            location = self.view.rowcol(self.view.sel()[0].begin())
            data = prepare_send_data(location, self.JEDI_COMMAND, 'jedi')
            data['settings'] = {
                'python_interpreter': get_settings(
                    self.view, 'python_interpreter', ''
                ),
            }
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

        if not data.get('result'):
            # fallback to ST3 builtin Goto Definition
            return self.view.window().run_command('goto_definition')

        symbols = []
        for result in data['result']:
            path = self._infere_context_data(result[1])
            symbols.append({
                'title': result[0],
                'location': 'File: {} Line: {} Column: {}'.format(
                    path, result[2], result[3]
                ),
                'position': '{}:{}:{}'.format(path, result[2], result[3])
            })

        ExplorerPanel(self.view, symbols).show([])

    def _infere_context_data(self, path: str) -> str:
        """If this is a remote session, infere context data if any
        """

        if is_remote_session(self.view):
            window = self.view.window().id()
            try:
                interpreter = Market().get(window).interpreter
            except Exception as e:
                print('while getting interp for Window ID {}: {}'.format(
                    window, e)
                )
                return path
            directory_map = interpreter.pathmap
            if directory_map is None:
                return path

            for local_dir, remote_dir in directory_map.items():
                if remote_dir in path:
                    return path.replace(remote_dir, local_dir)

        return path


class AnacondaGotoAssignment(AnacondaGoto):
    """Jedi GoTo a Python assignment for Sublime Text
    """
    JEDI_COMMAND = 'goto_assignment'


class AnacondaGotoPythonObject(AnacondaGoto):
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
