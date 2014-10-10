# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda pep257 wrapper
"""

import pep257


class PEP257(object):

    """PEP-257 class for Anaconda
    """

    def __init__(self, code, filename, ignore):
        self.code = code
        self.filename = filename
        self.ignore = [] if ignore is None else ignore

    def execute(self):
        """Check the code with pep257 to find errors
        """

        errors = []
        try:
            for error in pep257.PEP257Checker().check_source(
                self.code, self.filename
            ):
                error_code = getattr(error, 'code', None)
                if error_code is not None and error_code not in self.ignore:
                    errors.append(self._convert(error))
        except Exception:
            pass

        return errors

    def _convert(self, error):
        """
        Convert the error text returned back from pep257 into something
        that anaconda can understand.
        """

        return {
            'level': 'V',
            'lineno': error.line,
            'offset': 0,
            'code': error.code,
            'raw_error': '[V] PEP 257 ({0}): {1}'.format(
                error.code, error.message.split(': ', 1)[1]
            ),
            'message': '[V] PEP 257 (%s): %s',
            'underline_range': True
        }
