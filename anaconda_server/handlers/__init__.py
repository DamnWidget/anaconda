# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details


try:
    from qa_handler import QAHandler
    from jedi_handler import JediHandler
    from autoformat_handler import AutoFormatHandler
    from python_lint_handler import PythonLintHandler

except ImportError:  # Above imports do not work in python 3
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
