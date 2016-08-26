
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime_plugin

from ..anaconda_lib.helpers import get_settings, is_python


class AnacondaAutoformatPEP8EventListener(sublime_plugin.EventListener):
    """Anaconda AutoPEP8 formatter event listener class
    """

    def on_pre_save(self, view: sublime_plugin.sublime.View) -> None:
        """Called just before the file is going to be saved
        """

        if is_python(view) and get_settings(view, 'auto_formatting'):
            view.run_command('anaconda_auto_format')
