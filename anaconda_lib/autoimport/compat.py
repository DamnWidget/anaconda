"""Python versions compatibility module
"""

# Copyright (c) 2014 Oscar Campos
# This program is Free Software, take a look at the LICENSE for details

import sys

PY3 = True if sys.version_info > (3,) else False

if PY3:
    from io import StringIO
else:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

assert StringIO

__all__ = ["PY3", "StringIO"]
