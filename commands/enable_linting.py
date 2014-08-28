
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime_plugin

from ..anaconda_lib.helpers import get_settings
from ..anaconda_lib.helpers import valid_languages
from ..anaconda_lib.linting.sublime import ANACONDA, run_linter


class AnacondaEnableLinting(sublime_plugin.WindowCommand):
    """Disable the linting for the current buffer
    """

    def run(self):
        filename = self.window.active_view().file_name()
        if filename is not None and filename in ANACONDA['DISABLED']:
            ANACONDA['DISABLED'].remove(filename)

        run_linter(self.window.active_view())

    def is_enabled(self):
        """Determines if the command is enabled
        """

        view = self.window.active_view()
        if (view.file_name() not in ANACONDA['DISABLED']
                or not get_settings(view, 'anaconda_linting')):
            return False

        location = view.sel()[0].begin()
        for lang in valid_languages():
            matcher = 'source.{}'.format(lang)
            if view.match_selector(location, matcher) is True:
                return True

        return False
