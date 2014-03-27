
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

from .base import Command


class Lint(Command):
    """Run PyFlakes and Pep8 linters and return back results
    """

    def __init__(self, callback, uid, vid, linter, settings, code, filename):
        self.vid = vid
        self.code = code
        self.linter = linter
        self.settings = settings
        self.filename = filename
        super(Lint, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            self.callback({
                'success': True,
                'errors': self.linter.Linter().run_linter(
                    self.settings, self.code, self.filename),
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
