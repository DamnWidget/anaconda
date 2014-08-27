# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../anaconda_lib'))

from .qa_handler import QAHandler
from .jedi_handler import JediHandler
from .autoformat_handler import AutoFormatHandler
from .python_lint_handler import PythonLintHandler

ANACONDA_HANDLERS = {
    'qa': QAHandler,
    'jedi': JediHandler,
    'autoformat': AutoFormatHandler,
    'python_linter': PythonLintHandler
}


__all__ = [
    'QAHandler', 'JediHandler', 'AutoFormatHandler', 'PythonLintHandler',
    'ANACONDA_HANDLERS'
]
