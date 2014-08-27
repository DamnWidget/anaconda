# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda contexts
"""

import os
from contextlib import contextmanager


@contextmanager
def vagrant_root(directory):
    current_dir = os.getcwd()
    os.chdir(os.path.expanduser(directory))
    yield
    os.chdir(current_dir)
