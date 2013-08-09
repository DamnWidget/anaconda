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


def active_view():
    """Return the active view
    """

    return sublime.active_window().active_view()


def prepare_send_data(location):
    """Prepare dict that has to be sended trough the socket
    """

    view = active_view()
    return {
        'source': view.substr(sublime.Region(0, view.size())),
        'line': location[0] + 1,
        'offset': location[1],
        'filename': view.file_name() or ''
    }
