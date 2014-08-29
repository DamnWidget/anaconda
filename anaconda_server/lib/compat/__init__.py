
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sys

if sys.version_info >= (3, 0):
    from .python3 import AnacondaHandlerProvider
else:
    from python2 import AnacondaHandlerProvider


__all__ = ['AnacondaHandlerProvider']
