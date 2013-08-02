# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda decorators
"""

import time
import functools

from anaconda.utils import get_settings

MAX_RETRIES = 5


def only_python(func):
    """Execute the given function if we are on Python source only
    """

    @functools.wraps(func)
    def wrapper(self, view, *args, **kwargs):

        location = view.sel()[0].begin()
        matcher = 'source.python - string - comment'

        if view.match_selector(location, matcher):
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


def on_linting_vehabiour(modes):
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



def not_scratch(func):
    """Don't execute the given function if the view is scratched
    """

    @functools.wraps(func)
    def wrapper(self, view, *args, **kwargs):

        if not view.is_scratch():
            return func(self, view, *args, **kwargs)

    return wrapper


def executor(func):
    """Execute the underlying method retrying if needed
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = None
        retries = 0
        while retries < MAX_RETRIES:
            try:
                result = func(self, *args, **kwargs)
                break
            except Exception as error:
                retries += 1
                print(error)
                if self.proccess.poll() is None:
                    # proccess is ok, just retry
                    time.sleep(0.1)
                else:
                    # proccess died, restart
                    self.restart()
                    time.sleep(0.1)

        return result

    return wrapper
