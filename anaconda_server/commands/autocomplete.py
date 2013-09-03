
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

from base import Command, get_function_parameters

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
            data = self._parameters_for_complete()
            completions = self.script.completions()
            if DEBUG_MODE is True:
                logging.info(completions)
            data.extend([
                ('{0}\t{1}'.format(comp.name, comp.type), comp.name)
                for comp in completions
            ])
            self.callback({
                'success': True, 'completions': data, 'uid': self.uid
            })
        except Exception as error:
            logging.error('The underlying Jedi library as raised an exception')
            logging.error(error)
            logging.debug(traceback.format_exc().splitlines())
            self.callback({
                'success': False,
                'error': error,
                'uid': self.uid
            })

    def _parameters_for_complete(self):
        """Get function / class constructor paremeters completions list
        """

        completions = []
        try:
            in_call = self.script.call_signatures()[0]
        except IndexError:
            in_call = None

        parameters = get_function_parameters(in_call)

        for parameter in parameters:
            try:
                name, value = parameter
            except ValueError:
                name = parameter[0]
                value = None

            if value is None:
                completions.append((name, '${1:%s}' % name))
            else:
                completions.append(
                    (name + '\t' + value, '%s=${1:%s}' % (name, value))
                )

        return completions
