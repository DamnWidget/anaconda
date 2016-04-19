
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from functools import partial

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.jediusages import JediUsages
from ..anaconda_lib.helpers import prepare_send_data, is_python


class AnacondaGoto(sublime_plugin.TextCommand):
    """Jedi GoTo a Python defunition for Sublime Text
    """

    def run(self, edit):
        try:
            location = self.view.rowcol(self.view.sel()[0].begin())
            data = prepare_send_data(location, 'goto', 'jedi')
            Worker().execute(partial(JediUsages(self).process, False), **data)
        except:
            pass

    def is_enabled(self):
        """Determine if this command is enabled or not
        """

        return is_python(self.view)


class AnacondaGotoPythonObject(sublime_plugin.TextCommand):
    """Open prompt asking for Python path and JediGoto
    """

    def input_package(self, package):
        splitted = package.strip().split('.')
        if len(splitted) == 1:
            import_command = 'import %s' % splitted[0]
        else:
            import_command = 'from %s import %s' % (
                '.'.join(splitted[:-1]), splitted[-1]
            )
        self.goto_python_object(import_command)

    def goto_python_object(self, import_command):
        try:
            data = {
                'filename': '',
                'method': 'goto',
                'line': 1,
                'offset': len(import_command),
                'source': import_command,
                'handler': 'jedi'
            }
            Worker().execute(partial(JediUsages(self).process, False), **data)
        except:
            raise

    def run(self, edit):
        sublime.active_window().show_input_panel(
            'Provide object path:', '',
            self.input_package, None, None
        )
