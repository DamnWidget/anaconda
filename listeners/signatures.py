
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime_plugin

from functools import partial

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.helpers import prepare_send_data, is_python, get_settings


class AnacondaSignaturesEventListener(sublime_plugin.EventListener):
    """Signatures on status bar event listener class
    """

    documentation = None
    exclude = (
        'None', 'str', 'int', 'float', 'True', 'False', 'in', 'or', 'and')

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
            if self.documentation.split('(')[0] not in self.exclude:
                if self.documentation is not None and self.documentation != '':
                    self._show_status(view)
                    return

        view.erase_status('anaconda_doc')

    def _show_status(self, view):
        """Show message in the view status bar
        """

        view.set_status(
            'anaconda_doc', 'Anaconda: {}'.format(self.documentation)
        )
