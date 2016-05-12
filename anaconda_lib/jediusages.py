
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""Common jedi class to work with Jedi functions
"""

import sublime
from functools import partial


class JediUsages(object):
    """Work with Jedi definitions
    """

    def __init__(self, text):
        self.text = text

    def process(self, usages=False, data=None):
        """Process the definitions
        """

        view = self.text.view
        if not data['success']:
            sublime.status_message('Unable to find {}'.format(
                view.substr(view.word(view.sel()[0])))
            )
            return

        definitions = data['goto'] if not usages else data['usages']
        if len(definitions) == 0:
            sublime.status_message('Unable to find {}'.format(
                view.substr(view.word(view.sel()[0])))
            )
            return

        if definitions is not None and len(definitions) == 1 and not usages:
            self._jump(*definitions[0])
        else:
            self._show_options(definitions, usages)

    def _jump(self, filename, lineno=None, columno=None, transient=False):
        """Jump to a window
        """

        # process jumps from options window
        if type(filename) is int:
            if filename == -1:
                # restore view
                view = self.text.view
                point = self.point

                sublime.active_window().focus_view(view)
                view.show(point)

                if view.sel()[0] != point:
                    view.sel().clear()
                    view.sel().add(point)

                return

            filename, lineno, columno = self.options[filename]

        flags = sublime.ENCODED_POSITION
        if transient:
            flags |= sublime.TRANSIENT

        sublime.active_window().open_file(
            '{}:{}:{}'.format(filename, lineno or 0, columno or 0),
            flags
        )

        self._toggle_indicator(lineno, columno)

    def _show_options(self, defs, usages):
        """Show a dropdown quickpanel with options to jump
        """

        view = self.text.view
        if usages or (not usages and type(defs) is not str):
            options = [
                [o[0], 'line: {} column: {}'.format(o[1], o[2])] for o in defs
            ]
        else:
            if len(defs):
                options = defs[0]
            else:
                sublime.status_message('Unable to find {}'.format(
                    view.substr(view.word(view.sel()[0])))
                )
                return

        self.options = defs
        self.point = self.text.view.sel()[0]
        self.text.view.window().show_quick_panel(
            options, self._jump,
            on_highlight=partial(self._jump, transient=True)
        )

    def _toggle_indicator(self, lineno=0, columno=0):
        """Toggle mark indicator for focus the cursor
        """

        pt = self.text.view.text_point(lineno - 1, columno)
        region_name = 'anaconda.indicator.{}.{}'.format(
            self.text.view.id(), lineno
        )

        for i in range(3):
            delta = 300 * i * 2
            sublime.set_timeout(lambda: self.text.view.add_regions(
                region_name,
                [sublime.Region(pt, pt)],
                'comment',
                'bookmark',
                sublime.DRAW_EMPTY_AS_OVERWRITE
            ), delta)
            sublime.set_timeout(
                lambda: self.text.view.erase_regions(region_name),
                delta + 300
            )
