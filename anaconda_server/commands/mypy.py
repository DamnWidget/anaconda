
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

from .base import Command


class MyPy(Command):
    """Run mypy linter and return back results
    """

    def __init__(
            self, callback, uid, vid, linter,
            code, filename, mypypath, settings):
        self.vid = vid
        self.code = code
        self.filename = filename
        self.mypypath = mypypath
        self.settings = settings['mypy_settings']
        self.linter = linter
        super(MyPy, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            self.callback({
                'success': True,
                'errors': self.linter(
                    self.code, self.filename, self.mypypath, self.settings
                ).execute(),
                'uid': self.uid,
                'vid': self.vid,
            })
        except Exception as error:
            logging.error(error)
            logging.debug(traceback.format_exc())
            self.callback({
                'success': False,
                'error': error,
                'uid': self.uid,
                'vid': self.vid
            })
