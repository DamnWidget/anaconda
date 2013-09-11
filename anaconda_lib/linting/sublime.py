
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import re
import time
import threading
from functools import partial

import sublime

from . import pep8
from ..worker import Worker
from ..decorators import is_python
from ..helpers import get_settings, active_view

ANACONDA = {
    'ERRORS': {},
    'WARNINGS': {},
    'VIOLATIONS': {},
    'UNDERLINES': {},
    'LAST_PULSE': time.time(),
    'ALREADY_LINTED': False,
    'DISABLED': []
}

marks = {
    'warning': 'dot',
    'violation': 'dot',
    'illegal': 'circle'
}


###############################################################################
# Classes
###############################################################################
class TypeMonitor(threading.Thread):
    """Monitoring the typying
    """

    die = False

    def run(self):

        while not self.die:
            if not ANACONDA['ALREADY_LINTED']:
                view = sublime.active_window().active_view()
                if is_python(view):
                    delay = get_settings(view, 'anaconda_linter_delay', 0.5)
                    if time.time() - ANACONDA['LAST_PULSE'] >= delay:
                        ANACONDA['ALREADY_LINTED'] = True
                        run_linter(view)

            time.sleep(0.1)

monitor = TypeMonitor()


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

        ignore_star = self.view.settings().get(
            'pyflakes_ignore_import_*', True
        )

        for error in errors:
            error_level = error.get('level', 'W')
            messages = errors_level[error_level]['messages']
            underlines = errors_level[error_level]['underlines']

            if 'import *' in error['raw_error'] and ignore_star:
                continue

            self.add_message(
                error['lineno'], lines, error['raw_error'], messages
            )

            if error['pep8'] is True:
                self.underline_range(
                    error['lineno'], error['offset'], underlines
                )
            else:
                self.underline_regex(
                    lines=lines, underlines=underlines, **error
                )

        return {'lines': lines, 'results': errors_level}

    def parse_errors_pylint(self, errors):
        """Parse errores returned from the PyLint application
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

        for error_level, error_data in errors.items():
            messages = errors_level[error_level]['messages']
            # pylint does not return back offset for versions pre 1.0.0
            underlines = errors_level[error_level]['underlines']

            pylint_ignores = get_settings(self.view, 'pylint_ignore', [])
            for error in error_data:

                if error['code'] in pylint_ignores:
                    continue

                self.add_message(
                    error['line'], lines, error['message'], messages
                )
                if error['offset'] is not None:
                    self.underline_range(
                        error['line'], int(error['offset']), underlines
                    )

        return {'lines': lines, 'results': errors_level}


###############################################################################
# Global functions
###############################################################################
def erase_lint_marks(view):
    """Erase all the lint marks
    """

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

    for type_name, underlines in types.items():
        if len(underlines) > 0:
            view.add_regions(
                'anaconda-lint-underline-{}'.format(type_name), underlines,
                'anaconda.underline.{}'.format(type_name),
                flags=sublime.DRAW_EMPTY_AS_OVERWRITE
            )

    if len(lines) > 0:
        outline_style = {
            'outline': sublime.DRAW_OUTLINED,
            'none': sublime.HIDDEN,
            'fill': None
        }
        style = get_settings(view, 'anaconda_linter_mark_style', 'outline')
        gutter_theme = get_settings(view, 'anaconda_gutter_theme', 'basic')
        package_name = os.path.dirname(__file__).rsplit(os.path.sep, 3)[1]
        ico_path = (
            'Packages/' + package_name + '/anaconda_lib/linting/'
            '/gutter_mark_themes/{theme}-{type}.png'
        )

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


def run_linter(view):
    """Run the linter for the given view
    """

    if view.id() in ANACONDA['DISABLED']:
        return

    settings = {
        'pep8': get_settings(view, 'pep8', True),
        'pep8_ignore': get_settings(view, 'pep8_ignore', []),
        'pep8_max_line_length': get_settings(view, 'pep8_max_line_length',
                                             pep8.MAX_LINE_LENGTH),
        'pyflakes_ignore': get_settings(view, 'pyflakes_ignore', []),
        'pyflakes_disabled': get_settings(view, 'pyflakes_disabled', False)
    }
    text = view.substr(sublime.Region(0, view.size()))
    if get_settings(view, 'use_pylint', False) is False:
        data = {
            'code': text, 'settings': settings, 'filename': view.file_name()
        }
        data['method'] = 'run_linter'
    else:
        if view.file_name() is None:
            return
        data = {'filename': view.file_name()}
        data['method'] = 'run_linter_pylint'

    Worker().execute(partial(parse_results, view), **data)


def parse_results(view, data):
    """Parse the results from the server
    """

    if data and data['success'] is False:
        if get_settings(view, 'use_pylint', False) is True:
            print(data['errors'])
        return

    ERRORS = ANACONDA.get('ERRORS')
    WARNINGS = ANACONDA.get('WARNINGS')
    VIOLATIONS = ANACONDA.get('VIOLATIONS')
    UNDERLINES = ANACONDA.get('UNDERLINES')

    vid = view.id()
    ERRORS[vid] = {}
    WARNINGS[vid] = {}
    VIOLATIONS[vid] = {}

    if get_settings(view, 'use_pylint', False) is False:
        results = Linter(view).parse_errors(data['errors'])
    else:
        results = Linter(view).parse_errors_pylint(data['errors'])

    errors = results['results']
    lines = results['lines']

    UNDERLINES[vid] = errors['E']['underlines'][:]
    UNDERLINES[vid].extend(errors['V']['underlines'])
    UNDERLINES[vid].extend(errors['W']['underlines'])

    errors = {
        'error_underlines': errors['E']['underlines'],
        'warning_underlines': errors['W']['underlines'],
        'violation_underlines': errors['V']['underlines']
    }
    add_lint_marks(view, lines, **errors)

    update_statusbar(view)


def toggle_linting_behaviour():
    """Called when linting behaviour is changed
    """

    if get_settings(active_view(), 'anaconda_linting_behaviour') == 'always':
        monitor.die = False
        monitor.start()
    else:
        monitor.die = True
