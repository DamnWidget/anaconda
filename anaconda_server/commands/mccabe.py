
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

from .base import Command


class McCabe(Command):
    """Run McCabe complexity checker and return back results
    """

    def __init__(self, callback, uid, vid, mccabe, code, threshold, filename):
        self.vid = vid
        self.code = code
        self.filename = filename if filename is not None else ''
        self.threshold = threshold
        self.mccabe = mccabe(self.code, self.filename)
        super(McCabe, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            self.callback({
                'success': True,
                'errors': self.mccabe.get_code_complexity(self.threshold),
                'uid': self.uid,
                'vid': self.vid
            })
        except Exception as error:
            print(error)
            logging.error(error)
            logging.debug(traceback.format_exc().splitlines())
            self.callback({
                'success': False,
                'error': str(error),
                'uid': self.uid,
                'vid': self.vid
            })
