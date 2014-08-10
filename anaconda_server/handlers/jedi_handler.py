# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '../../anaconda_lib'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

import jedi
from anaconda_handler import AnacondaHandler
from jedi import refactoring as jedi_refactor
from commands import Doc, Goto, Rename, FindUsages
from commands import CompleteParameters, AutoComplete

logger = logging.getLogger('')


class JediHandler(AnacondaHandler):
    """Handle requests to execute Jedi related commands to the JsonServer

    The JsonServer instantiate an object of this class passing the method
    to execute as it came from the Sublime Text 3 Anaconda plugin
    """

    @property
    def script(self):
        """Generates a new valid Jedi Script and return it back
        """

        return self.jedi_script(**self.data)

    def jedi_script(self, source, line, offset, filename='', encoding='utf8'):
        """Generate an usable Jedi Script
        """

        if self.debug is True:
            logging.debug(
                'jedi_script called with the following parameters '
                'source: {0}\nline: {1} offset {2}, filename: {3}'.format(
                    source, line, offset, filename
                )
            )

        return jedi.Script(source, int(line), int(offset), filename, encoding)

    def rename(self, directories, new_word):
        """Rename the object under the cursor by the given word
        """

        Rename(
            self.callback, self.uid, self.script,
            directories, new_word, jedi_refactor
        )

    def autocomplete(self):
        """Call autocomplete
        """

        AutoComplete(self.callback, self.uid, self.script)

    def parameters(self, settings):
        """Call complete parameter
        """

        CompleteParameters(self.callback, self.uid, self.script, settings)

    def usages(self):
        """Call find usages
        """

        FindUsages(self.callback, self.uid, self.script)

    def goto(self):
        """Call goto
        """

        Goto(self.callback, self.uid, self.script)

    def doc(self):
        """Call doc
        """

        Doc(self.callback, self.uid, self.script)
