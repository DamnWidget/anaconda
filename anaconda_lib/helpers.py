# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda helpers
"""

import os
import json
import logging
import traceback
import subprocess

import sublime

NONE = 0x00
ONLY_PYTHON = 0x01
NOT_SCRATCH = 0x02
LINTING_ENABLED = 0x04


def check_linting(view, mask):
    """Check common linting constraints
    """

    if mask & ONLY_PYTHON and not is_python(view):
        return False

    if mask & NOT_SCRATCH and view.is_scratch():
        return False

    if (mask & LINTING_ENABLED
            and not get_settings(view, 'anaconda_linting', False)):
        return False

    return True


def check_linting_behaviour(view, behaviours):
    """Make sure the correct behaviours are applied
    """

    b = get_settings(view, 'anaconda_linting_behaviour', 'always')
    return b in behaviours


def is_python(view, ignore_comments=False):
    """Determine if the given view location is python code
    """

    if view is None:
        return False

    # disable linting in SublimeREPL
    if view.settings().get('repl', False):
        return

    try:
        location = view.sel()[0].begin()
    except IndexError:
        return False

    if ignore_comments is True:
        matcher = 'source.python'
    else:
        matcher = 'source.python - string - comment'

    return view.match_selector(location, matcher)


def create_subprocess(args, **kwargs):
    """Create a subprocess and return it back
    """

    if not 'cwd' in kwargs:
        kwargs['cwd'] = os.path.dirname(os.path.abspath(__file__))
    kwargs['bufsize'] = -1

    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs['startupinfo'] = startupinfo

    try:
        return subprocess.Popen(args, **kwargs)
    except:
        logging.error(
            'Your operating system denied the spawn of the anaconda jsonserver'
            ' process. Make sure your configured interpreter is a valid python'
            ' binary executable and is in the PATH'
        )


def get_settings(view, name, default=None):
    """Get settings
    """

    plugin_settings = sublime.load_settings('Anaconda.sublime-settings')

    if name in ('python_interpreter', 'extra_paths'):
        if view.window() is not None and view.window().folders():
            environfile = os.path.join(view.window().folders()[0], '.anaconda')
            if os.path.exists(environfile):
                with open(environfile, 'r') as jsonfile:
                    try:
                        data = json.loads(jsonfile.read())
                    except Exception as error:
                        print(error)
                    else:
                        return data.get(
                            name,
                            view.settings().get(name, plugin_settings.get(
                                name, default)
                            )
                        )

    return view.settings().get(name, plugin_settings.get(name, default))


def active_view():
    """Return the active view
    """

    return sublime.active_window().active_view()


def prepare_send_data(location, method):
    """Prepare dict that has to be sended trough the socket
    """

    view = active_view()
    return {
        'source': view.substr(sublime.Region(0, view.size())),
        'line': location[0] + 1,
        'offset': location[1],
        'filename': view.file_name() or '',
        'method': method
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
