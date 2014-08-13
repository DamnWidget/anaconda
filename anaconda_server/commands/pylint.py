
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

from .base import Command


class PyLint(Command):
    """Run PyLint and return back results
    """

    def __init__(self, callback, uid, vid, linter, rcfile, filename):
        self.vid = vid
        self.filename = filename
        self.linter = linter
        self.rcfile = rcfile
        super(PyLint, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            self.callback({
                'success': True,
                'errors': self.linter(
                    self.filename, self.rcfile).parse_errors(),
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
