
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib import worker, callback


class AnacondaBaseBuild(object):
    """Base class for all anaconda builders
    """

    def __init__(self, executable, *params):
        self.buffer = ""
        self.executable = executable
        self.params = params


class AnacondaPythonBuild(sublime_plugin.TextCommand):
    """Build the current buffer using the configured python interpreter
    """