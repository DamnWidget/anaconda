
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import re

import sublime
import sublime_plugin

from ..anaconda_lib.helpers import is_python
from ..anaconda_lib._typing import Tuple, Any  # noqa
from ..anaconda_lib.linting.sublime import ANACONDA


class AnacondaAutoImport(sublime_plugin.TextCommand):
    """Execute auto import for undefined names
    """

    def run(self, edit: sublime.Edit) -> None:

        self.data = None  # type: List[str]
        location = self.view.rowcol(self.view.sel()[0].begin())
        if not self._detected_undefined_name(location):
            sublime.message_dialog(
                'The word under the cursor is not an undefined name.')
            return

        for name in self.data:
            self.insert_import(edit, name)

    def is_enabled(self) -> bool:
        """Determine if this command is enabled or not
        """

        return is_python(self.view, True)

    def insert_import(self, edit: sublime.Edit, name: str) -> None:
        iline = self._guess_insertion_line()
        import_str = 'import {name}\n\n\n'.format(name=name)
        current_lines = self.view.lines(sublime.Region(0, self.view.size()))
        import_point = current_lines[iline].begin()

        self.view.insert(edit, import_point, import_str)

    def _guess_insertion_line(self) -> int:
        view_code = self.view.substr(sublime.Region(0, self.view.size()))
        match = re.search(r'^(@.+|def|class)\s+', view_code, re.M)
        if match is not None:
            code = view_code[:match.start()]
        else:
            # No class or function definition in this file, search for existing
            # import
            match = re.search(r'\s+.* tropmi', view_code[::-1], re.M)
            code = view_code[:len(view_code) - match.start()]

        return len(code.split('\n')) - 1

    def _detected_undefined_name(self, location: Tuple[int]) -> bool:
        vid = self.view.id()
        errors_mapping = {0: 'ERRORS', 1: 'WARNINGS', 2: 'VIOLATIONS'}
        for i, error_type in errors_mapping.items():
            for line, strings in ANACONDA[error_type].get(vid, {}).items():
                for string in strings:
                    if (location[0] == line and 'Undefined ' in string):
                        if self.data is None:
                            self.data = []

                        self.data.append(string.split('\'')[1])

        return False if self.data is None else True
