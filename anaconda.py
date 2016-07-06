# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda is a python autocompletion and linting plugin for Sublime Text 3
"""

import os
import sys
import logging
from string import Template

from .anaconda_lib import ioloop

from .commands import *
from .listeners import *

if sys.version_info < (3, 3):
    raise RuntimeError('Anaconda works with Sublime Text 3 only')

LOOP_RUNNING = False

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


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

    if not LOOP_RUNNING:
        ioloop.loop()


def plugin_unloaded() -> None:
    """Called directly from sublime on plugin unload
    """

    if LOOP_RUNNING:
        ioloop.terminate()
