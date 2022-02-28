# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details


from .base import Command, get_function_parameters


class CompleteParameters(Command):
    """Get back a python definition where to go"""

    def __init__(self, callback, line, col, uid, script, settings):
        self.script = script
        self.line = line
        self.col = col
        self.settings = settings
        super(CompleteParameters, self).__init__(callback, uid)

    def run(self):
        """Run the command"""

        completions = []
        complete_all = self.settings.get('complete_all_parameters', False)

        try:
            signatures = self.script.get_signatures(
                line=self.line, column=self.col
            )[0]
        except IndexError:
            signatures = None

        params = get_function_parameters(signatures)
        for i, p in enumerate(params):
            try:
                name, value = p
            except ValueError:
                name = p[0]
                value = None

            name = name.replace('param ', '')
            if value is None:
                completions.append('${%d:%s}' % (i + 1, name))
            else:
                if complete_all is True:
                    completions.append('%s=${%d:%s}' % (name, i + 1, value))

        self.callback(
            {
                'success': True,
                'template': ', '.join(completions),
                'uid': self.uid,
            }
        )
