
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import logging
import traceback

from .base import Command


class Rename(Command):
    """Get back a python definition where to go
    """

    def __init__(self, callback, uid, script, directories, new_word, refactor):
        self.script = script
        self.new_word = new_word
        self.jedi_refactor = refactor
        self.directories = directories
        super(Rename, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        renames = {}
        try:
            usages = self.script.usages()
            proposals = self.jedi_refactor.rename(self.script, self.new_word)
            for u in usages:
                path = os.path.dirname(u.module_path)
                if self.is_same_path(path):
                    if u.module_path not in renames:
                        renames[u.module_path] = []

                    thefile = proposals.new_files().get(u.module_path)
                    if thefile is None:
                        continue

                    lineno = u.line - 1
                    line = thefile.splitlines()[lineno]
                    renames[u.module_path].append({
                        'lineno': lineno, 'line': line
                    })
            success = True
        except Exception as error:
            logging.error(error)
            logging.debug(traceback.format_exc().splitlines())
            success = False

        self.callback({
            'success': success, 'renames': renames, 'uid': self.uid
        })

    def is_same_path(self, path):
        """Determines if the given path is a subdirectory of our paths
        """

        for directory in self.directories:
            if os.path.commonprefix([directory, path]) == directory:
                return True

        return False
