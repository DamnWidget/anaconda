
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

from .base import Command

DEBUG_MODE = False


class AutoComplete(Command):
    """Return Jedi completions
    """

    def __init__(self, callback, uid, script):
        self.script = script
        super(AutoComplete, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            completions = self.script.completions()
            if DEBUG_MODE is True:
                logging.info(completions)
            data = [
                ('{0}\t{1}'.format(comp.name, comp.type), comp.name)
                for comp in completions
            ]
            self.callback({
                'success': True, 'completions': data, 'uid': self.uid
            })
        except Exception as error:
            msg = 'The underlying Jedi library as raised an exception'
            logging.error(msg)
            logging.error(error)
            print(traceback.format_exc())
            if DEBUG_MODE:
                logging.debug(traceback.format_exc())

            self.callback({
                'success': False, 'error': str(error), 'uid': self.uid
            })
