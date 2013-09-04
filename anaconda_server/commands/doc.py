
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging

from .base import Command


class Doc(Command):
    """Get back a python definition where to go
    """

    def __init__(self, callback, uid, script):
        self.script = script
        super(Doc, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            definitions = self.script.goto_definitions()
        except Exception as error:
            logging.debug(error)
            definitions = []

        if not definitions:
            success = False
            docs = []
        else:
            success = True
            docs = [
                'Docstring for {0}\n{1}\n{2}'.format(
                    d.full_name, '=' * 40, d.doc
                ) if d.doc else 'No docstring for {0}'.format(d)
                for d in definitions
            ]

        self.callback({
            'success': success,
            'doc': ('\n' + '-' * 79 + '\n').join(docs),
            'uid': self.uid
        })
