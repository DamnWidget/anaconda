
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from functools import partial

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.tooltips import Tooltip
from ..anaconda_lib.helpers import prepare_send_data, is_python, get_settings


class AnacondaSignaturesEventListener(sublime_plugin.EventListener):
    """Signatures on status bar event listener class
    """

    documentation = None
    exclude = (
        'None', 'str', 'int', 'float', 'True',
        'False', 'in', 'or', 'and', 'bool'
    )

    def on_modified(self, view):
        """Called after changes has been made to a view
        """

        if not is_python(view) or not get_settings(view, 'display_signatures'):
            return

        try:
            location = view.rowcol(view.sel()[0].begin())
            if view.substr(view.sel()[0].begin()) in ['(', ')']:
                location = (location[0], location[1] - 1)

            data = prepare_send_data(location, 'doc', 'jedi')
            Worker().execute(partial(self.prepare_data, view), **data)
        except Exception as error:
            print(error)

    def prepare_data(self, view, data):
        """Prepare the returned data
        """

        if data['success'] and 'No docstring' not in data['doc']:
            self.documentation = data['doc'].splitlines()[2]
            if ('(' in self.documentation and
               self.documentation.split('(')[0].strip() not in self.exclude):
                if self.documentation is not None and self.documentation != '':
                    if get_settings(view, 'enable_signatures_tooltip', False):
                        return self._show_popup(view)

                    return self._show_status(view)

        if view.is_popup_visible():
            view.hide_popup()
        view.erase_status('anaconda_doc')

    def _show_popup(self, view):
        """Show message in a popup if sublime text version is >= 3070
        """

        st_ver = int(sublime.version())
        if st_ver >= 3070:
            css = get_settings(view, 'anaconda_tooltip_theme', 'dark')
            tooltip = Tooltip(css)
            content = {'content': self.documentation}
            kwargs = {'location': -1, 'max_width': 600}
            if st_ver >= 3071:
                kwargs['flags'] = sublime.COOPERATE_WITH_AUTO_COMPLETE
            text = tooltip.generate('signature', content)
            if text is not None:
                view.show_popup(text, **kwargs)
        else:
            self._show_status(view)

    def _show_status(self, view):
        """Show message in the view status bar
        """

        view.set_status(
            'anaconda_doc', 'Anaconda: {}'.format(self.documentation)
        )
