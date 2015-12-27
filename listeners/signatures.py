
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
from functools import partial

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.tooltips import Tooltip
from ..anaconda_lib.helpers import prepare_send_data, is_python, get_settings


class AnacondaSignaturesEventListener(sublime_plugin.EventListener):
    """Signatures on status bar event listener class
    """

    doc = None
    signature = None
    exclude = (
        'None', 'str', 'int', 'float', 'True',
        'False', 'in', 'or', 'and', 'bool'
    )

    def on_modified(self, view):
        """Called after changes has been made to a view
        """

        if view.command_history(0)[0] in ("expand_tabs", "unexpand_tabs"):
            return

        if not is_python(view) or not get_settings(view, 'display_signatures'):
            return

        try:
            location = view.rowcol(view.sel()[0].begin())
            if view.substr(view.sel()[0].begin()) in ['(', ')']:
                location = (location[0], location[1] - 1)

            data = prepare_send_data(location, 'doc', 'jedi')
            if int(sublime.version()) >= 3070:
                data['html'] = get_settings(
                    view, 'enable_signatures_tooltip', False)
            Worker().execute(partial(self.prepare_data, view), **data)
        except Exception as error:
            logging.error(error)

    def prepare_data(self, view, data):
        """Prepare the returned data
        """

        st_version = int(sublime.version())
        show_tooltip = get_settings(view, 'enable_signatures_tooltip', True)
        show_doc = get_settings(view, 'merge_signatures_and_doc', True)
        if data['success'] and 'No docstring' not in data['doc']:
            i = data['doc'].split('<br>').index("")
            if show_tooltip and show_doc and st_version >= 3070:
                self.doc = '<br>'.join(data['doc'].split('<br>')[i:])

            if not show_tooltip or st_version < 3070:
                self.signature = data['doc'].splitlines()[2]
            else:
                self.signature = '<br>&nbsp;&nbsp;&nbsp;&nbsp;'.join(
                    data['doc'].split('<br>')[0:i])
            if ('(' in self.signature and
                    self.signature.split('(')[0].strip() not in self.exclude):
                if self.signature is not None and self.signature != '':
                    if show_tooltip:
                        return self._show_popup(view)

                    return self._show_status(view)

        if st_version >= 3070:
            if view.is_popup_visible():
                view.hide_popup()
        view.erase_status('anaconda_doc')

    def _show_popup(self, view):
        """Show message in a popup if sublime text version is >= 3070
        """

        show_doc = get_settings(view, 'merge_signatures_and_doc', True)
        content = {'content': self.signature}
        display_tooltip = 'signature'
        if show_doc:
            content = {'signature': self.signature, 'doc': self.doc}
            display_tooltip = 'signature_doc'

        css = get_settings(view, 'anaconda_tooltip_theme', 'dark')
        Tooltip(css).show_tooltip(
            view, display_tooltip, content, partial(self._show_status, view))

    def _show_status(self, view):
        """Show message in the view status bar
        """

        view.set_status(
            'anaconda_doc', 'Anaconda: {}'.format(self.signature)
        )
