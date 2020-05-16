
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import re
import time
from functools import partial

import sublime

from . import pycodestyle as pep8
from ..worker import Worker
from ..callback import Callback
from ..persistent_list import PersistentList
from ..helpers import (
    get_settings, is_code, get_view, check_linting, LINTING_ENABLED
)
from ..phantoms import Phantom


sublime_api = sublime.sublime_api

ANACONDA = {
    'ERRORS': {},
    'WARNINGS': {},
    'VIOLATIONS': {},
    'UNDERLINES': {},
    'LAST_PULSE': time.time(),
    'ALREADY_LINTED': False,
    'DISABLED': PersistentList(),
    'DISABLED_BUFFERS': []
}

marks = {
    'warning': 'dot',
    'violation': 'dot',
    'illegal': 'circle'
}


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

        # Remove trailing period from error message unless the message is "can't import ."
        if message.endswith('.') and not message.endswith("import ."):
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
            region = sublime.Region(position + i)
            if self.is_that_code(region.begin()):
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
                kwargs.get('wordmatch') is None or
                r.group('underline') == kwargs.get('wordmatch')
            )
        ]

        # make the lineno one-based again for underline_range
        lineno += 1
        for start, end in results:
            self.underline_range(
                lineno, start + offset, kwargs['underlines'], end - start
            )

    def is_that_code(self, point):
        """Determines if the given region is valid Python code
        """

        matcher = 'source.python - string - comment'
        return self.view.match_selector(point, matcher)

    def parse_errors(self, errors):
        """Parse errors returned from the PyFlakes and pep8 libraries
        """

        vid = self.view.id()

        errors_level = {
            'E': {'messages': ANACONDA.get('ERRORS')[vid], 'underlines': []},
            'W': {'messages': ANACONDA.get('WARNINGS')[vid], 'underlines': []},
            'V': {
                'messages': ANACONDA.get('VIOLATIONS')[vid], 'underlines': []
            }
        }

        lines = set()
        if errors is None:
            return {'lines': lines, 'results': errors_level}

        ignore_star = get_settings(self.view, 'pyflakes_ignore_import_*', True)

        for error in errors:
            try:
                line_text = self.view.substr(self.view.full_line(
                    self.view.text_point(error['lineno']-1, 0)
                ))
                if '# noqa' in line_text:
                    continue
            except Exception as e:
                print(e)

            error_level = error.get('level', 'W')
            messages = errors_level[error_level]['messages']
            underlines = errors_level[error_level]['underlines']
            if 'raw_error' not in error:
                error['raw_error'] = error['message']

            if 'import *' in error['raw_error'] and ignore_star:
                continue

            self.add_message(
                error['lineno'], lines, error['raw_error'], messages
            )

            if error['underline_range'] is True:
                self.underline_range(
                    error['lineno'], error['offset'], underlines
                )
            elif error.get('len') is not None and error.get('regex') is None:
                self.underline_range(
                    error['lineno'], error['offset'],
                    underlines, error['len']
                )
            else:
                self.underline_regex(
                    lines=lines, underlines=underlines, **error
                )

        return {'lines': lines, 'results': errors_level}


###############################################################################
# Global functions
###############################################################################
def erase_lint_marks(view):
    """Erase all the lint marks
    """
    if get_settings(view, 'anaconda_linter_phantoms', False):
        Phantom().clear_phantoms(view)

    types = ['illegal', 'warning', 'violation']
    for t in types:
        view.erase_regions('anaconda-lint-underline-{}'.format(t))
        view.erase_regions('anaconda-lint-outlines-{}'.format(t))


def add_lint_marks(view, lines, **errors):
    """Adds lint marks to view on the given lines.
    """

    erase_lint_marks(view)
    types = {
        'warning': errors['warning_underlines'],
        'illegal': errors['error_underlines'],
        'violation': errors['violation_underlines'],
    }
    style = get_settings(view, 'anaconda_linter_mark_style', 'outline')
    show_underlines = get_settings(view, 'anaconda_linter_underlines', True)
    if show_underlines:
        for type_name, underlines in types.items():
            if len(underlines) > 0:
                view.add_regions(
                    'anaconda-lint-underline-{}'.format(type_name), underlines,
                    'anaconda.underline.{}'.format(type_name),
                    flags=sublime.DRAW_EMPTY_AS_OVERWRITE
                )

    if len(lines) > 0:
        outline_style = {
            'solid_underline': sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SOLID_UNDERLINE,        # noqa
            'stippled_underline': sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_STIPPLED_UNDERLINE,  # noqa
            'squiggly_underline': sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SQUIGGLY_UNDERLINE,  # noqa
            'outline': sublime.DRAW_OUTLINED,
            'none': sublime.HIDDEN,
            'fill': None
        }
        gutter_theme = get_settings(
            view, 'anaconda_gutter_theme', 'basic').lower()
        package_name = os.path.dirname(__file__).rsplit(os.path.sep, 3)[1]
        ico_path = (
            'Packages/' + package_name + '/anaconda_lib/linting/'
            'gutter_mark_themes/{theme}-{type}.png'
        )

        if get_settings(view, 'anaconda_linter_phantoms', False):
            phantom = Phantom()
            vid = view.id()
            phantoms = []
            for level in ['ERRORS', 'WARNINGS', 'VIOLATIONS']:
                for line, messages in ANACONDA.get(level)[vid].items():
                    for message in messages:
                        phantoms.append({
                            "line": line,
                            "level": level.lower(),
                            "messages": message
                        })
            phantom.update_phantoms(view, phantoms)

        for lint_type, lints in get_outlines(view).items():
            if len(lints) > 0:
                if get_settings(view, 'anaconda_gutter_marks', False):
                    if gutter_theme == 'basic':
                        gutter_marks = marks[lint_type]
                    else:
                        gutter_marks = ico_path.format(theme=gutter_theme,
                                                       type=lint_type)
                else:
                    gutter_marks = ''

                args = [
                    'anaconda-lint-outlines-{}'.format(lint_type),
                    lints,
                    'anaconda.outline.{}'.format(lint_type),
                    gutter_marks
                ]
                draw_style = outline_style.get(style, sublime.DRAW_OUTLINED)
                if draw_style is not None:
                    args.append(draw_style)

                view.add_regions(*args)


def get_outlines(view):
    """Return outlines for the given view
    """

    ERRORS = ANACONDA.get('ERRORS')
    WARNINGS = ANACONDA.get('WARNINGS')
    VIOLATIONS = ANACONDA.get('VIOLATIONS')

    vid = view.id()
    return {
        'warning': [
            view.full_line(view.text_point(l, 0)) for l in WARNINGS[vid]
        ],
        'illegal': [
            view.full_line(view.text_point(l, 0)) for l in ERRORS[vid]
        ],
        'violation': [
            view.full_line(view.text_point(l, 0)) for l in VIOLATIONS[vid]
        ]
    }


def last_selected_lineno(view):
    """Return back the last selected line number
    """

    sel = view.sel()
    return None if sel is None else view.rowcol(sel[0].end())[0]


def update_statusbar(view):
    """Updates the status bar
    """

    errors = get_lineno_msgs(view, last_selected_lineno(view))
    if len(errors) > 0:
        view.set_status('Linter', '; '.join(errors))
    else:
        view.erase_status('Linter')


def get_lineno_msgs(view, lineno):
    """Get lineno error messages and return it back
    """

    ERRORS = ANACONDA.get('ERRORS')
    WARNINGS = ANACONDA.get('WARNINGS')
    VIOLATIONS = ANACONDA.get('VIOLATIONS')

    errors_msg = []
    if lineno is not None:
        vid = view.id()
        if vid in ERRORS:
            errors_msg.extend(ERRORS[vid].get(lineno, []))
        if vid in WARNINGS:
            errors_msg.extend(WARNINGS[vid].get(lineno, []))
        if vid in VIOLATIONS:
            errors_msg.extend(VIOLATIONS[vid].get(lineno, []))

    return errors_msg


def run_linter(view=None, hook=None):
    """Run the linter for the given view
    """

    if view is None:
        view = sublime.active_window().active_view()

    window_view = (sublime.active_window().id(), view.id())
    if (view.file_name() in ANACONDA['DISABLED']
            or window_view in ANACONDA['DISABLED_BUFFERS']):
        erase_lint_marks(view)
        return

    settings = {
        'pep8': get_settings(view, 'pep8', True),
        'pep8_ignore': get_settings(view, 'pep8_ignore', []),
        'pep8_max_line_length': get_settings(
            view, 'pep8_max_line_length', pep8.MAX_LINE_LENGTH),
        'pep8_error_levels': get_settings(view, 'pep8_error_levels', None),
        'pyflakes_ignore': get_settings(view, 'pyflakes_ignore', []),
        'pyflakes_disabled': get_settings(
            view, 'pyflakes_disabled', False),
        'use_pylint': get_settings(view, 'use_pylint', False),
        'use_pep257': get_settings(view, 'pep257', False),
        'validate_imports': get_settings(view, 'validate_imports', False),
        'pep257_ignore': get_settings(view, 'pep257_ignore', []),
        'pep8_rcfile': get_settings(view, 'pep8_rcfile'),
        'pylint_rcfile': get_settings(view, 'pylint_rcfile'),
        'pylint_ignores': get_settings(view, 'pylint_ignore'),
        'pyflakes_explicit_ignore': get_settings(
            view, 'pyflakes_explicit_ignore', []),
        'use_mypy': get_settings(view, 'mypy', False),
        'mypy_settings': get_mypy_settings(view),
        'mypypath': get_settings(view, 'mypy_mypypath', ''),
        'python_interpreter': get_settings(view, 'python_interpreter', ''),
    }

    text = view.substr(sublime.Region(0, view.size()))
    data = {
        'vid': view.id(),
        'code': text,
        'settings': settings,
        'filename': view.file_name(),
        'method': 'lint',
        'handler': 'python_linter'
    }

    if hook is None:
        Worker().execute(Callback(on_success=parse_results), **data)
    else:
        Worker().execute(Callback(partial(hook, parse_results)), **data)


def get_mypy_settings(view):
    """Get MyPy related settings
    """

    mypy_settings = []
    if get_settings(view, 'mypy_silent_imports', False):
        mypy_settings.append('--ignore-missing-imports')
        mypy_settings.append('--follow-imports=skip')
    if get_settings(view, 'mypy_almost_silent', False):
        mypy_settings.append('--follow-imports=error')
    if get_settings(view, 'mypy_py2', False):
        mypy_settings.append('--py2')
    if get_settings(view, 'mypy_disallow_untyped_calls', False):
        mypy_settings.append('--disallow-untyped-calls')
    if get_settings(view, 'mypy_disallow_untyped_defs', False):
        mypy_settings.append('--disallow-untyped-defs')
    if get_settings(view, 'mypy_check_untyped_defs', False):
        mypy_settings.append('--check-untyped-defs')
    if get_settings(view, 'mypy_fast_parser', False):
        mypy_settings.append('--fast-parser')
    custom_typing = get_settings(view, 'mypy_custom_typing', None)
    if custom_typing is not None:
        mypy_settings.append('--custom-typing')
        mypy_settings.append(custom_typing)

    mypy_settings.append('--incremental')  # use cache always
    mypy_settings.append(
        get_settings(view, 'mypy_suppress_stub_warnings', False)
    )

    return mypy_settings


def parse_results(data, code='python'):
    """Parse the results from the server
    """

    view = get_view(sublime.active_window(), data['vid'])
    if data and data['success'] is False or not is_code(view, code, True):
        if get_settings(view, 'use_pylint', False) is True:
            for p in data['errors']:
                print(p)
        return

    # Check if linting was disabled between now and when the request was sent
    # to the server.
    window_view = (sublime.active_window().id(), view.id())
    if (not check_linting(view, LINTING_ENABLED) or
            view.file_name() in ANACONDA['DISABLED']
            or window_view in ANACONDA['DISABLED_BUFFERS']):
        return

    vid = view.id()
    ANACONDA['ERRORS'][vid] = {}
    ANACONDA['WARNINGS'][vid] = {}
    ANACONDA['VIOLATIONS'][vid] = {}

    results = Linter(view).parse_errors(data['errors'])
    errors = results['results']
    lines = results['lines']

    ANACONDA['UNDERLINES'][vid] = errors['E']['underlines'][:]
    ANACONDA['UNDERLINES'][vid].extend(errors['V']['underlines'])
    ANACONDA['UNDERLINES'][vid].extend(errors['W']['underlines'])

    errors = {
        'error_underlines': errors['E']['underlines'],
        'warning_underlines': errors['W']['underlines'],
        'violation_underlines': errors['V']['underlines']
    }
    add_lint_marks(view, lines, **errors)
    update_statusbar(view)
