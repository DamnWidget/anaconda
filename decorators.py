# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda decorators
"""

import functools


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
