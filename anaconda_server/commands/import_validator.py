
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

from .base import Command


class ImportValidator(Command):
    """Run the ImportValidate to detect invalid imports
    """

    def __init__(self, callback, uid, vid, linter, code, filename, settings):
        self.vid = vid
        self.code = code
        self.linter = linter
        self.filename = filename
        self.settings = settings
        super(ImportValidator, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """
        try:
            v = self.linter(self.code, self.filename, self.settings)
            self.callback({
                'success': True,
                'errors': [] if v.is_valid() else self._convert(v),
                'uid': self.uid,
                'vid': self.vid
            })
        except Exception as error:
            logging.error(error)
            logging.debug(traceback.format_exc().splitlines())
            self.callback({
                'success': False,
                'error': error,
                'uid': self.uid,
                'vid': self.vid
            })

    def _convert(self, validator):
        """Build report for the validator
        """

        errors = []
        for line, lineno in validator.errors:
            errors.append({
                'level': 'E',
                'lineno': lineno,
                'offset': 0,
                'code': 801,
                'raw_error': '[E] ImportValidator (801): {0}'.format(line),
                'message': '[E] ImportValidator (%s): %s',
                'underline_range': True
            })

        return errors
