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
from functools import cmp_to_key

import sublime
import sublime_plugin

from anaconda.anaconda import get_settings
from anaconda.linting.pyflakes import messages as pyflakes_messages
from anaconda.linting.linter import Pep8Error, Pep8Warning, OffsetError
from anaconda.decorators import only_python, not_scratch, on_linting_enabled

errors = {}
warnings = {}
violations = {}
underlines = {}

marks = {
    'warning': 'dot',
    'violation': 'dot',
    'illegal': 'circle'
}


###############################################################################
# Anaconda Linter Plugin Subclasses
###############################################################################
class BackgroundLinter(sublime_plugin.EventListener):
    """Background linter, can be turned off via plugin settings
    """

    def __init__(self):
        super(BackgroundLinter, self).__init__()
        self.last_selected_line = -1

    @only_python
    @not_scratch
    @on_linting_enabled
    def on_modified_async(self, view):
        """
        Called after changes have been made to a view.
        Runs in a separate thread, and does not block the application.
        """

        # update the last selected line number
        self.last_selected_line = -1
        run_linter(view)

    def _erase_marks(self, view):
        """Just a wrapper for erase_lint_marks
        """

        erase_lint_marks(view)


###############################################################################
# Classes
###############################################################################
class Linter:
    """Linter class that can interacts with Sublime Linter GUI
    """

    def __init__(self, view):
        self.view = view

    def add_message(self, lineno, lines, message, messages):
        # assume lineno is one-based, ST3 wants zero-based line numbers

        lineno -= 1
        lines.add(lineno)
        message = message[0].upper() + message[1:]

        # Remove trailing period from error message
        if message[-1] == '.':
            message = message[:-1]

        if lineno in messages:
            messages[lineno].append(message)
        else:
            messages[lineno] = [message]

    def underline_range(self, lineno, position, underlines, length=1):
        # assume lineno is one-based, ST3 wants zero-based line numbers

        lineno -= 1
        line = self.view.full_line(self.view.text_point(lineno, 0))
        position += line.begin()

        for i in range(length):
            underlines.append(sublime.Region(position + i))

    def underline_regex(self, **kwargs):
        # assume lineno is one-based, ST3 wants zero-based line numbers

        offset = 0
        lineno = kwargs.get('lineno', 1) - 1
        kwargs.get('lines', set()).add(lineno)
        line = self.view.full_line(self.view.text_point(lineno, 0))
        line_text = self.view.substr(line)

        if kwargs.get('linematch') is not None:
            match = re.match(kwargs['linematch'], line_text)

            if match is not None:
                line_text = match.group('match')
                offset = match.start('match')
            else:
                return

        iters = re.finditer(kwargs.get('regex'), line_text)
        results = [
            (r.start('underline'), r.end('underline')) for r in iters if (
                kwargs.get('wordmatch') is None
                or r.group('underline') == kwargs.get('wordmatch')
            )
        ]

        # make the lineno one-based again for underline_range
        lineno += 1
        for start, end in results:
            self.underline_range(
                lineno, start + offset, kwargs['underlines'], end - start
            )

    def parse_errors(self, errors, **kwargs):
        """Parse errors returned from the PyFlakes and pep8 libraries
        """

        lines = set()
        errors.sort(key=cmp_to_key(lambda a, b: a.lineno < b.lineno))
        ignore_star = self.view.settings().get(
            'pyflakes_ignore_import_*', True
        )

        for error in errors:
            error_level = 'W' if not hasattr(error, 'level') else error.level
            messages, underlines = self._get_errors_level(
                error_level, **kwargs
            )

            if type(error) is pyflakes_messages.ImportStarUsed and ignore_star:
                continue

            self.add_message(error.lineno, lines, str(error), messages)
            if type(error) in [Pep8Warning, Pep8Error, OffsetError]:
                self.underline_range(
                    self.view, error.lineno, error.offset, underlines
                )
            elif type(error) in [
                    pyflakes_messages.RedefinedWhileUnused,
                    pyflakes_messages.UndefinedName,
                    pyflakes_messages.UndefinedExport,
                    pyflakes_messages.UndefinedLocal,
                    pyflakes_messages.Redefined,
                    pyflakes_messages.UnusedVariable]:
                regex = (
                    r'((and|or|not|if|elif|while|in)\s+|[+\-*^%%<>=\(\{{])*\s'
                    '*(?P<underline>[\w\.]*{0}[\w]*)'.format(re.escape(
                        error.message_args[0]
                    ))
                )
                self.underline_regex(
                    lineno=error.lineno, regex=regex, lines=lines,
                    underlines=underlines, wordmatch=error.message_args[0]
                )
            elif type(error) is pyflakes_messages.ImportShadowByLoopVar:
                regex = 'for\s+(?P<underline>[\w]*{0}[\w*])'.format(
                    re.escape(error.message_args[0])
                )
                self.underline_regex(
                    lineno=error.lineno, regex=regex, lines=lines,
                    underlines=underlines, wordmatch=error.message_args[0]
                )
            elif type(error) in [
                    pyflakes_messages.UnusedImport,
                    pyflakes_messages.ImportStarUsed]:
                if type(error) is pyflakes_messages.ImportStarUsed:
                    word = '*'
                else:
                    word = error.message_args[0]

                linematch = '(from\s+[\w_\.]+\s+)?import\s+(?P<match>[^#;]+)'
                regex = '(^|\s+|,\s*|as\s+)(?P<underline>[\w]*{0}[\w]*)'
                regex.format(re.escape(word))

                self.underline_regex(
                    lineno=error.lineno, regex=regex, lines=lines,
                    underlines=underlines, wordmatch=word,
                    linematch=linematch
                )
            elif type(error) is pyflakes_messages.DuplicateArgument:
                regex = 'def [\w_]+\(.*?(?P<underline>[\w]*{0}[\w]*)'.format(
                    re.escape(error.message_args[0])
                )
                self.underline_regex(
                    lineno=error.lineno, regex=regex, lines=lines,
                    underlines=underlines, wordmatch=error.message_args[0]
                )
            elif type(error) is pyflakes_messages.LateFutureImport:
                pass
            else:
                print('Oops, we missed an error type!', type(error))

        return lines

    def _get_errors_level(self, error_level):
        """Return back the correct error levels for messages and unserlines
        """

        messages, underlines = self.error_level_mapper.get(error_level)
        return messages[self.view.id()], underlines[self.view.id()]


###############################################################################
# Global functions
###############################################################################
def erase_lint_marks(view):
    """Erase all the lint marks
    """

    types = ['illegal', 'warning', 'violation']
    for t in types:
        view.erase_regions('lint-underline-{}'.format(t))
        view.erase_regions('lint-outlines-{}'.format(t))
    view.erase_regions('lint-annotations')


def add_lint_marks(view, lines, **errors):
    """Adds lint marks to view on the given lines.
    """

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

    if len(lines) > 0:
        outline_style = {'none': sublime.HIDDEN}
        style = get_settings(view, 'anaconda_linter_mark_style', 'outline')

        for lint_type, lints in get_outlines(view).items():
            if len(lints) > 0:
                args = [
                    'lint-outlines-{}'.format(lint_type),
                    lints,
                    'anaconda.outline.{}'.format(lint_type),
                    marks[lint_type],
                    outline_style.get(style, sublime.DRAW_OUTLINE)
                ]

                view.add_regions(*args)


def get_outlines(view):
    """Return outlines for the given view
    """

    vid = view.id()
    return {
        'warning': [
            view.full_line(view.text_point(l, 0)) for l in warnings[vid]
        ],
        'illegal': [
            view.full_line(view.text_point(l, 0)) for l in errors[vid]
        ],
        'violation': [
            view.full_line(view.text_point(l, 0)) for l in violations[vid]
        ]
    }


def run_linter(view):
    """Run the linter for the given view
    """

    vid = view.id()
    errors[vid] = {}
    warnings[vid] = {}
    violations[vid] = {}

    start = time.time()
    text = view.substr(sublime.Region(0, view.size()))
