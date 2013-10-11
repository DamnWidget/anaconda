# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda decorators
"""

import sys
import time
import pstats
import functools

try:
    import cProfile
    CPROFILE_AVAILABLE = True
except ImportError:
    CPROFILE_AVAILABLE = False

try:
    import sublime
    from .helpers import get_settings, project_name
except ImportError:
    # we just imported the file from jsonserver so we don't need get_settings
    pass


def is_python(view, ignore_comments=False):
    """Determine if the given view location is python code
    """

    if view is None:
        return False

    try:
        location = view.sel()[0].begin()
    except IndexError:
        return False

    if ignore_comments is True:
        matcher = 'source.python'
    else:
        matcher = 'source.python - string - comment'
    return view.match_selector(location, matcher)


def on_vagrant_enabled(func):
    """Execute the given function only if vagrant is enabled
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):

        if self.view.settings().get('vagrant_environment') is not None:
            return func(self, *args, **kwargs)

    return wrapper


def enable_for_python(func):
    """Returns True or False depending if we are in python sources
    """

    @functools.wraps(func)
    def wrapper(self):

        if is_python(self.view):
            return True

        return False

    return wrapper


def only_python(func):
    """Execute the given function if we are on Python source only
    """

    @functools.wraps(func)
    def wrapper(self, view, *args, **kwargs):

        if is_python(view):
            return func(self, view, *args, **kwargs)

    return wrapper


def on_linting_enabled(func):
    """Execute the given function if linting is enabled only
    """

    @functools.wraps(func)
    def wrapper(self, view, *args, **kwargs):

        if get_settings(view, 'anaconda_linting', False) is True:
            return func(self, view, *args, **kwargs)
        else:
            # erase all the linter marks if any
            self._erase_marks(view)

    return wrapper


def on_linting_behaviour(modes):
    """Make sure the correct behaviours are applied
    """

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            view = args[1]
            b = get_settings(view, 'anaconda_linting_behaviour', 'always')
            if b in modes:
                return func(*args, **kwargs)
            else:
                self._erase_marks(view)

        return wrapper

    return decorator


def on_auto_formatting_enabled(func):
    """Executed only when auto_formatting is True in the configuration
    """

    @functools.wraps(func)
    def wrapper(self, view, *args, **kwargs):

        if get_settings(view, 'auto_formatting', False) is True:
            return func(self, view, *args, **kwargs)

    return wrapper


def auto_project_switch(func):
    """Auto kill and start a new jsonserver on project switching
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):

        wid = sublime.active_window().id()
        view = sublime.active_window().active_view()
        if (
            get_settings(view, 'auto_project_switch', False) and
            self.project_name != 'anaconda-{id}'.format(id=wid) and
            project_name() != self.project_name
        ):
                print('Project switch detected...')
                self.reconnecting = True
                self.start()
        else:
            func(self, *args, **kwargs)

    return wrapper


def not_scratch(func):
    """Don't execute the given function if the view is scratched
    """

    @functools.wraps(func)
    def wrapper(self, view, *args, **kwargs):

        if not view.is_scratch():
            return func(self, view, *args, **kwargs)

    return wrapper


def timeit(logger):
    """Decorator for timeit timeit timeit
    """

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            starttime = time.time()
            result = func(*args, **kwargs)
            endtime = time.time()
            total = endtime - starttime
            logger.debug(
                'Func {} took {} secs'.format(func.__name__, total)
            )

            return result

        return wrapper

    return decorator


def profile(func):
    """Run the profiler in the given function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        view = sublime.active_window().active_view()

        if get_settings(view, 'anaconda_debug', False) == 'profiler':

            if CPROFILE_AVAILABLE:
                pr = cProfile.Profile()
                pr.enable()
                result = func(*args, **kwargs)
                pr.disable()
                ps = pstats.Stats(pr, stream=sys.stdout)
                ps.sort_stats('time')
                ps.print_stats(15)
            else:
                print(
                    'cProfile doesn\'t seems to can be imported on ST3 + {}, '
                    'sorry. You may want to use @timeit instead, so sorry '
                    'really'.format(sys.platform)
                )
                result = func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        return result

    return wrapper
