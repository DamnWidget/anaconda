
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib import worker


class AnacondaVagrantEnable(sublime_plugin.WindowCommand):
    """Enable Vagrant on this window/project
    """

    def run(self):
        vagrant_worker = worker.WORKERS.get(sublime.active_window().id())
        if vagrant_worker is not None:
            vagrant_worker.support = True
