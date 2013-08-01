# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda utils
"""

import sublime


def get_settings(view, name, default=None):
    """Get settings
    """

    plugin_settings = sublime.load_settings('Anaconda.sublime-settings')
    return view.settings().get(name, plugin_settings.get(name, default))