
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from .base import Command


class Goto(Command):
    """Get back a python definition where to go
    """

    def __init__(self, callback, uid, script):
        self.script = script
        super(Goto, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            definitions = self.script.goto_assignments()
            if all(d.type == 'import' for d in definitions):
                definitions = self.script.goto_definitions()
        except:
            data = None
            success = False
        else:
            data = [(i.module_path, i.line, i.column + 1)
                    for i in definitions if not i.in_builtin_module()]
            success = True

        self.callback({'success': success, 'goto': data, 'uid': self.uid})
