
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
from functools import partial

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.tooltips import Tooltip
from ..anaconda_lib.kite import Integration
from ..anaconda_lib._typing import Dict, Tuple, Any
from ..anaconda_lib.helpers import prepare_send_data, is_python, get_settings


class AnacondaSignaturesEventListener(sublime_plugin.EventListener):
    """Signatures on status bar event listener class
    """

    doc = None  # type: str
    signature = None
    exclude = (
        'None', 'NoneType', 'str', 'int', 'float', 'True',
        'False', 'in', 'or', 'and', 'bool'
    )

    def on_modified(self, view: sublime.View) -> None:
        """Called after changes has been made to a view
        """

        if view.command_history(0)[0] in ("expand_tabs", "unexpand_tabs"):
            return

        if not is_python(view) or not get_settings(view, 'display_signatures'):
            return

        if Integration.enabled():
            return

        try:
            location = view.rowcol(view.sel()[0].begin())
            if view.substr(view.sel()[0].begin()) in ['(', ')']:
                location = (location[0], location[1] - 1)

            data = prepare_send_data(location, 'doc', 'jedi')
            use_tooltips = get_settings(
                view, 'enable_signatures_tooltip', True
            )
            st_version = int(sublime.version())
            if st_version >= 3070:
                data['html'] = use_tooltips

            currying = partial(self.prepare_data_status, view)
            if use_tooltips and st_version >= 3070:
                currying = partial(self.prepare_data_tooltip, view)

            data["settings"] = {
                'python_interpreter': get_settings(view, 'python_interpreter', '')
            }
            Worker().execute(currying, **data)
        except Exception as error:
            logging.error(error)

    def prepare_data_tooltip(
            self, view: sublime.View, data: Dict[str, Any]) -> Any:
        """Prepare the returned data for tooltips
        """

        merge_doc = get_settings(view, 'merge_signatures_and_doc')
        if (data['success'] and 'No docstring' not
                in data['doc'] and data['doc'] != 'list\n'):
            try:
                i = data['doc'].split('<br>').index("")
            except ValueError:
                self.signature = data['doc']
                self.doc = ''
                if self._signature_excluded(self.signature):
                    return
                return self._show_popup(view)

            if merge_doc:
                self.doc = '<br>'.join(data['doc'].split('<br>')[i:]).replace(
                    "  ", "&nbsp;&nbsp;")

            self.signature = '<br>&nbsp;&nbsp;&nbsp;&nbsp;'.join(
                data['doc'].split('<br>')[0:i])
            if self.signature is not None and self.signature != "":
                if not self._signature_excluded(self.signature):
                    return self._show_popup(view)

        if view.is_popup_visible():
            view.hide_popup()
        view.erase_status('anaconda_doc')

    def prepare_data_status(
            self, view: sublime.View, data: Dict[str, Any]) -> Any:
        """Prepare the returned data for status
        """

        if (data['success'] and 'No docstring' not
                in data['doc'] and data['doc'] != 'list\n'):
            self.signature = data['doc']
            if self._signature_excluded(self.signature):
                return
            try:
                self.signature = self.signature.splitlines()[2]
            except KeyError:
                return

            return self._show_status(view)

    def _show_popup(self, view: sublime.View) -> None:
        """Show message in a popup if sublime text version is >= 3070
        """

        show_doc = get_settings(view, 'merge_signatures_and_doc', True)
        content = {'content': self.signature}
        display_tooltip = 'signature'
        if show_doc:
            content = {'signature': self.signature, 'doc': self.doc}
            display_tooltip = 'signature_doc'

        css = get_settings(view, 'anaconda_tooltip_theme', 'popup')
        Tooltip(css).show_tooltip(
            view, display_tooltip, content, partial(self._show_status, view))

    def _show_status(self, view: sublime.View) -> None:
        """Show message in the view status bar
        """

        view.set_status(
            'anaconda_doc', 'Anaconda: {}'.format(self.signature)
        )

    def _signature_excluded(self, signature: str) -> Tuple[str]:
        """Whether to supress displaying information for the given signature.
        """

        # Check for the empty string first so the indexing in the next tests
        # can't hit an exception, and we don't want to show an empty signature.
        return ((signature == "") or
                (signature.split('(', 1)[0].strip() in self.exclude) or
                (signature.lstrip().split(None, 1)[0] in self.exclude))
