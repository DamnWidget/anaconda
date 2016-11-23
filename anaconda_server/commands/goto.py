
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from .base import Command


class Goto(Command):
    """Get back a python definition where to go
    """

    def __init__(self, callback, uid, script):
        self.script = script
        super(Goto, self).__init__(callback, uid)

    def _get_definitions(self):
        definitions = self.script.goto_assignments()
        if all(d.type == 'import' for d in definitions):
            definitions = self.script.goto_definitions()
        return definitions

    def run(self):
        """Run the command
        """

        try:
            definitions = self._get_definitions()
        except:
            data = []
            success = False
        else:
            # we use a set here to avoid duplication
            data = set([(i.full_name, i.module_path, i.line, i.column + 1)
                        for i in definitions if not i.in_builtin_module()])

            success = True

        self.callback(
            {'success': success, 'result': list(data), 'uid': self.uid})


class GotoAssignment(Goto):
    """Get back a python assignment where to go
    """

    def _get_definitions(self):
        return self.script.goto_assignments()
