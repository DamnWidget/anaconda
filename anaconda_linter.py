# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda is a python autocompletion and linting plugin for Sublime Text 3
"""

import re
import time
import threading
from functools import partial

import sublime
import sublime_plugin

from anaconda.anaconda import Worker
from anaconda.utils import get_settings
from anaconda.decorators import (
    only_python, not_scratch, on_linting_enabled, on_linting_vehabiour
)

ANACONDA = {
    'QUEUE': {},
    'ERRORS': {},
    'WARNINGS': {},
    'VIOLATIONS': {},
    'UNDERLINES': {},
    'TIMES': {}
}

# For snappier linting, different delays are used for different linting times:
# (linting time, delays)
DELAYS = (
    (50, (50, 100)),
    (100, (100, 300)),
    (200, (200, 500)),
    (400, (400, 1000)),
    (800, (800, 2000)),
    (1600, (1600, 3000)),
)

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
    @on_linting_vehabiour(['always'])
    def on_modified_async(self, view):
        """
        Called after changes have been made to a view.
        Runs in a separate thread, and does not block the application.
        """
        # update the last selected line number
        self.last_selected_line = -1
        queue_linter(view)

    @only_python
    @on_linting_enabled
    @on_linting_vehabiour(['always', 'load-save'])
    def on_load_async(self, view):
        """Called after load a file
        """

        queue_linter(view)

    @only_python
    @not_scratch
    @on_linting_enabled
    def on_post_save_async(self, view):
        """Called post file save event
        """

        queue_linter(view)

    @only_python
    @not_scratch
    @on_linting_enabled
    def on_selection_modified_async(self, view):
        """Called on selection modified
        """

        # on movement, delay queue (to make movement responsive)
        delay_queue(1000)
        last_selected_line = last_selected_lineno(view)

        if last_selected_line != self.last_selected_line:
            self.last_selected_line = last_selected_line
            update_statusbar(view)

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


###############################################################################
# Global functions
###############################################################################
def get_delay(t, view):
    """Get the delay for the related view
    """

    delay = 0
    for _t, d in DELAYS:
        if _t <= t:
            delay = d

    delay = delay or DELAYS[0][1]

    # If the user specifies a delay greater than the built in delay,
    # figure they only want to see marks when idle.
    min_delay = get_settings(view, 'anaconda_linter_delay', 0) * 1000

    if min_delay > delay[1]:
        erase_lint_marks(view)

    return (min_delay, min_delay) if min_delay > delay[1] else delay


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
        outline_style = {'none': sublime.HIDDEN}
        style = get_settings(view, 'anaconda_linter_mark_style', 'outline')

        for lint_type, lints in get_outlines(view).items():
            if len(lints) > 0:
                if get_settings(view, 'anaconda_gutter_marks', False):
                    gutter_marks = marks[lint_type]
                else:
                    gutter_marks = ''

                args = [
                    'anaconda-lint-outlines-{}'.format(lint_type),
                    lints,
                    'anaconda.outline.{}'.format(lint_type),
                    gutter_marks,
                    outline_style.get(style, sublime.DRAW_OUTLINED)
                ]

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

    TIMES = ANACONDA.get('TIMES')
    ERRORS = ANACONDA.get('ERRORS')
    WARNINGS = ANACONDA.get('WARNINGS')
    VIOLATIONS = ANACONDA.get('VIOLATIONS')
    UNDERLINES = ANACONDA.get('UNDERLINES')

    vid = view.id()
    ERRORS[vid] = {}
    WARNINGS[vid] = {}
    VIOLATIONS[vid] = {}

    start = time.time()
    settings = {
        'pep8': get_settings(view, 'pep8', True),
        'pep8_ignore': get_settings(view, 'pep8_ignore', []),
        'pyflakes_ignore': get_settings(view, 'pyflakes_ignore', []),
        'pyflaked_disabled': get_settings(view, 'pyflakes_disabled', False)
    }
    text = view.substr(sublime.Region(0, view.size()))

    results = Linter(view).parse_errors(
        Worker.lookup(view).run_linter(text, settings, view.file_name())
    )

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
    end = time.time()
    TIMES[vid] = (end - start) * 1000


def queue_linter(view, timeout=-1, preemptive=False, event=None):
    """Put the current view in a queue to be examined by a linter
    """

    TIMES = ANACONDA.get('TIMES')

    if preemptive:
        timeout = busy_timeout = 0
    elif timeout == -1:
        timeout, busy_timeout = get_delay(TIMES.get(view.id(), 100), view)
    else:
        busy_timeout = timeout

    kwargs = {
        'timeout': timeout,
        'busy_timeout': busy_timeout,
        'preemptive': preemptive,
        'event': event
    }
    queue(view, partial(
        _update_view, view, view.file_name(), **kwargs), kwargs
    )


def _update_view(view, filename, **kwargs):
    """
    It is possible that by the time the queue is run,
    the original file is no longer being displayed in the view,
    or the view may be gone. This happens especially when
    viewing files temporarily by single-clicking on a filename
    in the sidebar or when selecting a file through the choose file palette.
    """

    valid_view = False
    view_id = view.id()

    for window in sublime.windows():
        for v in window.views():
            if v.id() == view_id:
                valid_view = True
                break

    if not valid_view or view.is_loading() or view.file_name() != filename:
        return

    try:
        run_linter(view)
    except RuntimeError as error:
        print(error)


def _callback(view, filename, kwargs):
    kwargs['callback'](view, filename, **kwargs)


def background_linter():
    __lock_.acquire()

    QUEUE = ANACONDA.get('QUEUE')

    try:
        callbacks = list(QUEUE.values())
        QUEUE.clear()
    finally:
        __lock_.release()

    for callback in callbacks:
        sublime.set_timeout(callback, 0)


###############################################################################
# SublimeLinter's Queue dispatcher system - (To be revisited later)
###############################################################################
queue_dispatcher = background_linter
queue_thread_name = 'background linter'
MAX_DELAY = 10


def queue(view, callback, kwargs):
    """Queue lint calls
    """

    global __signaled_, __signaled_first_
    now = time.time()
    __lock_.acquire()
    QUEUE = ANACONDA.get('QUEUE')

    try:
        QUEUE[view.id()] = callback
        timeout = kwargs['timeout']
        busy_timeout = kwargs['busy_timeout']

        if now < __signaled_ + timeout * 4:
            timeout = busy_timeout or timeout

        __signaled_ = now
        _delay_queue(timeout, kwargs['preemptive'])

        if not __signaled_first_:
            __signaled_first_ = __signaled_
    finally:
        __lock_.release()


def queue_loop():
    """
    An infinite loop running the linter in a background thread meant to
    update the view after user modifies it and then does no further
    modifications for some time as to not slow down the UI with linting
    """

    global __signaled_, __signaled_first_

    while __loop_:
        __semaphore_.acquire()
        __signaled_first_ = 0
        __signaled_ = 0
        queue_dispatcher()


def delay_queue(timeout):
    __lock_.acquire()
    try:
        _delay_queue(timeout, False)
    finally:
        __lock_.release()


def _delay_queue(timeout, preemptive):
    global __signaled_, __queued_
    now = time.time()

    if not preemptive and now <= __queued_ + 0.01:
        return  # never delay queues too fast (except preemptively)

    __queued_ = now
    _timeout = float(timeout) / 1000

    if __signaled_first_:
        if MAX_DELAY > 0 and now - __signaled_first_ + _timeout > MAX_DELAY:
            _timeout -= now - __signaled_first_
            if _timeout < 0:
                _timeout = 0
            timeout = int(round(_timeout * 1000, 0))

    new__signaled_ = now + _timeout - 0.01

    if __signaled_ >= now - 0.01 and (
            preemptive or new__signaled_ >= __signaled_ - 0.01):
        __signaled_ = new__signaled_

        def _signal():
            if time.time() < __signaled_:
                return
            __semaphore_.release()

        sublime.set_timeout(_signal, timeout)

# only start the thread once - otherwise the plugin will get laggy
# when saving it often.
__semaphore_ = threading.Semaphore(0)
__lock_ = threading.Lock()
__queued_ = 0
__signaled_ = 0
__signaled_first_ = 0

# First finalize old standing threads:
__loop_ = False
__pre_initialized_ = False


def queue_finalize(timeout=None):
    global __pre_initialized_

    for thread in threading.enumerate():
        if thread.isAlive() and thread.name == queue_thread_name:
            __pre_initialized_ = True
            thread.__semaphore_.release()
            thread.join(timeout)

queue_finalize()

# Initialize background thread:
__loop_ = True
__active_linter_thread = threading.Thread(
    target=queue_loop, name=queue_thread_name
)
__active_linter_thread.__semaphore_ = __semaphore_
__active_linter_thread.start()
