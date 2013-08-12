# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda utils
"""

import os
import traceback

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


def project_name():
        """
        Generates and returns back a valid project name for the window

        If there is not worker yet for this window, we create it and set a
        name for it. If we don't have a project file we just use the first
        folder name in the window's folders as name, if we don't have any
        folders in the window we just use the window.window_id
        """

        window = sublime.active_window()
        project_name = window.project_file_name()
        if project_name is None:
            folders = window.folders()
            if len(folders) > 0:
                project_name = window.folders()[0].rsplit(os.sep, 1)[1]
            else:
                project_name = 'anaconda-{id}'.format(id=window.window_id)
        else:
            project_name = project_name.rsplit(os.sep, 1)[1].split('.')[0]

        return project_name


def get_traceback():
    """Get traceback log
    """

    traceback_log = []
    for traceback_line in traceback.format_exc().splitlines():
        traceback_log.append(traceback_line)

    return '\n'.join(traceback_log)