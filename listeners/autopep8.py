
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime_plugin

from ..anaconda_lib.decorators import only_python, on_auto_formatting_enabled


class AnacondaAutoformatPEP8EventListener(sublime_plugin.EventListener):
    """Anaconda AutoPEP8 formatter event listener class
    """

    @only_python
    @on_auto_formatting_enabled
    def on_pre_save_async(self, view):
        """Called just before the file is going to be saved
        """

        view.run_command('anaconda_auto_format')
