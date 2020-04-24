# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda is a python autocompletion and linting plugin for Sublime Text 3
"""

import os
import sys
import shutil
import logging
from string import Template

import sublime
import sublime_plugin

from .anaconda_lib import ioloop
from .anaconda_lib.helpers import get_settings

from .commands import *   # noqa
from .listeners import *  # noqa

if sys.version_info < (3, 3):
    raise RuntimeError('Anaconda works with Sublime Text 3 only')

DISABLED_PLUGINS = []
LOOP_RUNNING = False

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

CURRENT_PATH = os.path.dirname( os.path.realpath( __file__ ) )


def plugin_loaded() -> None:
    """Called directly from sublime on plugin load
    """

    package_folder = os.path.dirname(__file__)
    if not os.path.exists(os.path.join(package_folder, 'Main.sublime-menu')):
        template_file = os.path.join(
            package_folder, 'templates', 'Main.sublime-menu.tpl'
        )
        with open(template_file, 'r', encoding='utf8') as tplfile:
            template = Template(tplfile.read())

        menu_file = os.path.join(package_folder, 'Main.sublime-menu')
        with open(menu_file, 'w', encoding='utf8') as menu:
            menu.write(template.safe_substitute({
                'package_folder': os.path.basename(package_folder)
            }))

    # unload any conflictive package while anaconda is running
    sublime.set_timeout_async(monitor_plugins, 0)

    if not LOOP_RUNNING:
        ioloop.loop()

    install_context_menu()
    disable_linter_context_menu()

def install_context_menu():
    origin  = os.path.join( CURRENT_PATH, 'Base Context.sublime-menu' )
    destine = os.path.join( CURRENT_PATH, 'Context.sublime-menu' )

    shutil.copy( origin, destine )

class HideMenuOnActivation(sublime_plugin.EventListener):

    def on_activated_async(self, view):
        disable_linter_context_menu()

def disable_linter_context_menu():
    """
        Disable the linter Context Menu, if not on a linter view.

        Allow to hide .sublime-menu folders
        https://github.com/SublimeTextIssues/Core/issues/1859
    """
    origin  = os.path.join( CURRENT_PATH, 'Context.sublime-menu' )
    destine = os.path.join( CURRENT_PATH, 'Context.sublime-menu-hidden' )

    try:
        if is_current_view_linted( sublime.active_window().active_view() ):
            shutil.move( destine, origin )

        else:
            shutil.move( origin, destine )

    except IOError:
        pass

def is_current_view_linted(view):
    return view.match_selector( view.sel()[0].begin(), 'source.python')

def plugin_unloaded() -> None:
    """Called directly from sublime on plugin unload
    """

    # reenable any conflictive package
    enable_plugins()

    if LOOP_RUNNING:
        ioloop.terminate()


def monitor_plugins():
    """Monitor for any plugin that conflicts with anaconda
    """

    view = sublime.active_window().active_view()
    if not get_settings(view, 'auto_unload_conflictive_plugins', True):
        return

    plist = [
        'Jedi - Python autocompletion',  # breaks auto completion
        'SublimePythonIDE',  # interfere with autocompletion
        'SublimeCodeIntel'  # breaks everything, SCI is a mess
    ]

    for plugin in plist:
        if plugin in sys.modules:
            [
                sublime_plugin.unload_module(m) for k, m in sys.modules.items()
                if plugin in k
            ]
            if plugin not in DISABLED_PLUGINS:
                DISABLED_PLUGINS.append(plugin)

    sublime.set_timeout_async(monitor_plugins, 5 * 60 * 1000)


def enable_plugins():
    """Reenable disabled plugins by anaconda
    """

    for plugin in DISABLED_PLUGINS:
        sublime_plugin.reload_plugin(plugin)
