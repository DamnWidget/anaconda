
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging
import traceback

from .base import Command, get_function_parameters

DEBUG_MODE = False


class AutoComplete(Command):
    """Return Jedi completions
    """

    def __init__(self, callback, uid, script, settings):
        self.script = script
        self.settings = settings
        super(AutoComplete, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            completions = self.script.completions()
            if DEBUG_MODE:
                logging.info(completions)

            data = self._format_completions(completions)
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

    def _format_completions(self, cpls):
        """Format the completions from jedi
        """

        lguide = self._calculate_lguide(cpls)
        return [
            ('{0}{1} {2}'.format(
                cpl.name, ' ' * (lguide - len(cpl.name)),
                cpl.type
            ), self._snippet(cpl)) for cpl in cpls
        ]

    def _snippet(self, cpl):
        """Compose an snippet for the auto completion
        """

        if not hasattr(cpl, 'params'):
            return ''

        snippet = []
        complete_all = self.settings.get('complete_all_parameters', False)

        params = get_function_parameters(cpl)
        for i, p in enumerate(params):
            try:
                name, value = p
            except ValueError:
                name = p[0]
                value = None

            if not value:
                snippet.append('${%d:%s}' % (i + 1, name))
            elif complete_all:
                snippet.append('%s=${%d:%s}' % (name, i + 1, value))

        return ', '.join(snippet)

    def _calculate_lguide(self, cpls):
        """Calculate the max string for the completions and return it back
        """

        lguide = 0
        for elem in cpls:
            try:
                lguide = max(lguide, len(elem.name))
            except AttributeError:
                lguide = max(lguide, len(elem[0]))

        return lguide

    def run_old(self):
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
