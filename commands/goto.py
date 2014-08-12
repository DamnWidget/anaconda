
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from functools import partial

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
