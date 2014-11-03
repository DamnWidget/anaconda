
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime_plugin

from ..anaconda_lin.helpers import get_settings, is_python


class AnacondaAutoImportEventListener(sublime_plugin.EventListener):
    """Anaconda AutoImport event listener class
    """

    def on_pre_save(self, view):
        """Called just before the file is going to be saved
        """

        if is_python(view) and get_settings(view, 'autoimport'):
            view.run_command('anaconad_auto_import')
