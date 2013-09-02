# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda contexts
"""

import json
from contextlib import contextmanager


@contextmanager
def json_decode(data):
    data = data.replace(b'\t', b'\\t')
    try:
        yield json.loads(data.decode('utf8'))
    except ValueError:
        try:
            yield eval(data)
        except Exception:
            yield str(data.decode('utf8'))
