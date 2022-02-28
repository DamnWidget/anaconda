# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from .base import Command


class FindUsages(Command):
    """Get back a python usages for the given object"""

    def __init__(self, callback, line, col, uid, script):
        self.script = script
        self.line = line
        self.col = col
        super(FindUsages, self).__init__(callback, uid)

    def run(self):
        """Run the command"""

        try:
            usages = self.script.get_references(
                line=self.line, column=self.col
            )
            success = True
        except:
            usages = None
            success = False

        try:
            self.callback(
                {
                    'success': success,
                    'result': [
                        (i.full_name, i.module_path, i.line, i.column)
                        for i in usages
                        if not i.in_builtin_module()
                    ]
                    if usages is not None
                    else [],
                    'uid': self.uid,
                }
            )
        except ValueError:
            self.callback(
                {
                    'success': success,
                    'result': [
                        (i.name, i.module_path, i.line, i.column)
                        for i in usages
                        if not i.in_builtin_module()
                    ]
                    if usages is not None
                    else [],
                    'uid': self.uid,
                }
            )
