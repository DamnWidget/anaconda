
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime_plugin

from ..anaconda_lib.helpers import get_settings
from ..anaconda_lib.helpers import valid_languages
from ..anaconda_lib.linting.sublime import ANACONDA, erase_lint_marks, run_linter


class AnacondaToggleLinting(sublime_plugin.WindowCommand):
    """Toggle the linting for the current buffer
    """

    def run(self) -> None:
        view = self.window.active_view()
        filename = view.file_name()
        window_view = (self.window.id(), view.id())

        if filename is not None:

            if filename in ANACONDA['DISABLED']:
                ANACONDA['DISABLED'].remove(filename)
                run_linter(view)
            else:
                ANACONDA['DISABLED'].append(filename)
                erase_lint_marks(view)

        else:

            if window_view in ANACONDA['DISABLED_BUFFERS']:
                ANACONDA['DISABLED_BUFFERS'].remove(window_view)
                run_linter(view)
            else:
                ANACONDA['DISABLED_BUFFERS'].append(window_view)
                erase_lint_marks(view)
