
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from functools import partial

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib._typing import Dict, Any
from ..anaconda_lib.tooltips import Tooltip
from ..anaconda_lib.callback import Callback
from ..anaconda_lib.helpers import prepare_send_data, is_python, get_settings


class AnacondaDoc(sublime_plugin.TextCommand):
    """Jedi get documentation string for Sublime Text
    """

    documentation = None

    def run(self, edit: sublime.Edit) -> None:
        if self.documentation is None:
            try:
                location = self.view.rowcol(self.view.sel()[0].begin())
                if self.view.substr(self.view.sel()[0].begin()) in ['(', ')']:
                    location = (location[0], location[1] - 1)

                data = prepare_send_data(location, 'doc', 'jedi')
                if int(sublime.version()) >= 3070:
                    data['html'] = get_settings(
                        self.view, 'enable_docstrings_tooltip', False)
                Worker().execute(
                    Callback(on_success=self.prepare_data), **data
                )
            except Exception as error:
                print(error)
        else:
            if get_settings(self.view, 'enable_docstrings_tooltip', False) \
               and int(sublime.version()) >= 3070:
                self.print_popup(edit)
            else:
                self.print_doc(edit)

    def is_enabled(self) -> bool:
        """Determine if this command is enabled or not
        """

        return is_python(self.view)

    def prepare_data(self, data: Dict[str, Any]) -> None:
        """Prepare the returned data
        """

        if data['success']:
            self.documentation = data['doc']
            if self.documentation is None or self.documentation == '':
                self._show_status()
            else:
                sublime.active_window().run_command(self.name())
        else:
            self._show_status()

    def print_doc(self, edit: sublime.Edit) -> None:
        """Print the documentation string into a Sublime Text panel
        """

        doc_panel = self.view.window().create_output_panel(
            'anaconda_documentation'
        )

        doc_panel.set_read_only(False)
        region = sublime.Region(0, doc_panel.size())
        doc_panel.erase(edit, region)
        doc_panel.insert(edit, 0, self.documentation)
        self.documentation = None
        doc_panel.set_read_only(True)
        doc_panel.show(0)
        self.view.window().run_command(
            'show_panel', {'panel': 'output.anaconda_documentation'}
        )

    def print_popup(self, edit) -> None:
        """Show message in a popup
        """

        dlines = self.documentation.splitlines()
        name = dlines[0]
        docstring = ''.join(dlines[1:])
        content = {'name': name, 'content': docstring}
        self.documentation = None
        css = get_settings(self.view, 'anaconda_tooltip_theme', 'popup')
        Tooltip(css).show_tooltip(
            self.view, 'doc', content, partial(self.print_doc, edit))

    def _show_status(self) -> None:
        """Show message in the view status bar
        """

        self.view.set_status(
            'anaconda_doc', 'Anaconda: No documentation found'
        )
        sublime.set_timeout_async(
            lambda: self.view.erase_status('anaconda_doc'), 5000
        )
