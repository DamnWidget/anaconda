
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
            assignments = self.script.goto_assignments()
            if all(d.type == 'import' for d in assignments):
                definitions = filter(lambda x: not x.in_builtin_module(),
                                     self.script.goto_definitions())
                if not definitions:
                    definitions = assignments
            else:
                definitions = assignments
        except:
            data = None
            success = False
        else:
            # we use a set here to avoid duplication
            data = set([(i.full_name, i.module_path, i.line, i.column + 1)
                        for i in definitions])
            success = True

        self.callback(
            {'success': success, 'result': list(data), 'uid': self.uid})
