
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

from .base import Command


class PEP257(Command):
    """Run pep257 linter and return back results
    """

    def __init__(self, callback, uid, vid, linter, ignore, code, filename):
        self.vid = vid
        self.code = code
        self.filename = filename
        self.ignore = ignore
        self.linter = linter
        super(PEP257, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            self.callback({
                'success': True,
                'errors': self.linter(
                    self.code, self.filename, self.ignore).execute(),
                'uid': self.uid,
                'vid': self.vid,
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
