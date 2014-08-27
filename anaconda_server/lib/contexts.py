
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""Anaconda JsonServer contexts
"""

import sys
import json
from contextlib import contextmanager


@contextmanager
def json_decode(data):
    PY26 = False
    data = data.replace(b'\t', b'\\t')
    if sys.version_info < (2, 6, 5):
        PY26 = True
        fixed_keys = {}
    try:
        if PY26:
            for k, v in json.loads(data.decode('utf8')).iteritems():
                fixed_keys[str(k)] = v
            yield fixed_keys
        else:
            yield json.loads(data.decode('utf8'))
    except ValueError:
        try:
            yield eval(data)
        except Exception:
            yield str(data.decode('utf8'))
