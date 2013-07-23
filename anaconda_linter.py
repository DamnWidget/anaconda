# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda is a python autocompletion and linting plugin for Sublime Text 3
"""

import os
import re
import sys
import pickle
import threading

import sublime
import sublime_plugin

errors = {}
warnings = {}
violations = {}
underlines = {}

marks = {
    'warning': ('', 'dot'),
    'violation': ('', 'dot'),
    'illegal': ('', 'circle')
}


def add_lint_marks(view, lines, **errors):
    """Adds lint marks to view on the given lines.
    """

    vid = view.id()
    erase_lint_marks(view)
    types = {
        'warning': errors['warning_underlines'],
        'illegal': errors['illegal_underlines'],
        'violation': errors['violation_underlines'],
    }

    for type_name, underlines in types.items():
        if len(underlines) > 0:
            view.add_regions(
                'lint-underline-{}'.format(type_name),
                underlines,
                'anaconda.underline.{}'.format(type_name),
                flags=sublime.DRAW_EMPTY_AS_OVERWRITE
            )
