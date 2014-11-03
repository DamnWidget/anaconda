
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.jsonclient import Callback
from ..anaconda_lib.progress_bar import ProgressBar
from ..anaconda_lib.helpers import is_python, get_settings


class AnacondaAutoImport(sublime_plugin.TextCommand):
    """Execute auto import for undefined names
    """

    import_data = None

    def run(self, edit):
        """Run the autoimport command
        """

        if self.import_data is not None:
            self.update_imports(edit)
            self.import_data = None
            return

        code = self.view.substr(sublime.Region(0, self.view.size()))
        try:
            messages = {
                'start': 'Autoimporting please wait...',
                'end': 'Autoimport fix done!',
                'fail': 'Autoimport failed, buffer unchanged.',
                'timeout': 'Autoimport failed, buffer unchanged.'
            }
            self.pbar = ProgressBar(messages)
            self.pbar.start()

            data = {
                'vid': self.view.id(),
                'code': code,
                'method': 'autoimport',
                'handler': 'autoimport'
            }
            timeout = get_settings(self.view, 'auto_import_timeout', 1)

            callback = Callback(timeout=timeout)
            callback.on(success=self.prepare_imports)
            callback.on(error=self.on_failure)
            callback.on(timeout=self.on_timeout)

            Worker().execute(callback, **data)
        except:
            logging.error(traceback.format_exc())

    def prepare_imports(self, data):
        """Collect the returned data and prepare the imports
        """

        self.import_data = data
        self.pbar.terminate()
        self.view.run_command('anaconda_auto_import')

    def is_enabled(self):
        """Determine if this command is enabled or not
        """

        return is_python(self.view, True)

    def update_imports(self, edit):
        """Update the imports block
        """

        line_start = self.import_data['line_start']
        line_end = self.import_data['line_end']
        import_block = self.import_data['import_block']

        buffer_lines = self.view.lines(sublime.Region(0, self.view.size()))
        start = buffer_lines[line_start].begin()
        end = buffer_lines[line_end].end()
        self.view.erase(edit, sublime.Region(start, end))
        self.view.insert(edit, buffer_lines[line_start].begin(), import_block)
