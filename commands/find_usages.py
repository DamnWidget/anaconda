
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from functools import partial

import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.callback import Callback
from ..anaconda_lib.jediusages import JediUsages
from ..anaconda_lib.helpers import prepare_send_data, active_view, is_python


class AnacondaFindUsages(sublime_plugin.TextCommand):
    """Jedi find usages for Sublime Text
    """

    def run(self, edit: sublime_plugin.sublime.Edit) -> None:
        try:
            location = active_view().rowcol(self.view.sel()[0].begin())
            data = prepare_send_data(location, 'usages', 'jedi')
            Worker().execute(
                Callback(on_success=partial(JediUsages(self).process, True)),
                **data
            )
        except:
            pass

    def is_enabled(self) -> bool:
        """Determine if this command is enabled or not
        """

        return is_python(self.view)
