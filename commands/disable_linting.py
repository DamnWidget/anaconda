
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime_plugin

from ..anaconda_lib.helpers import get_settings
from ..anaconda_lib.helpers import valid_languages
from ..anaconda_lib.linting.sublime import ANACONDA, erase_lint_marks


class AnacondaDisableLinting(sublime_plugin.WindowCommand):
    """Disable the linting for the current buffer
    """

    def run(self) -> None:
        view = self.window.active_view()
        if view.file_name() is not None:
            ANACONDA['DISABLED'].append(view.file_name())
        else:
            ANACONDA['DISABLED_BUFFERS'].append((self.window.id(), view.id()))

        erase_lint_marks(view)

    def is_enabled(self) -> bool:
        """Determines if the command is enabled
        """

        view = self.window.active_view()
        if ((view.file_name() in ANACONDA['DISABLED']
                and view.id() in ANACONDA['DISABLED_BUFFERS'])
                or not get_settings(view, 'anaconda_linting')):
            return False

        location = view.sel()[0].begin()
        for lang in valid_languages():
            matcher = 'source.{}'.format(lang)
            if view.match_selector(location, matcher) is True:
                return True

        return False
