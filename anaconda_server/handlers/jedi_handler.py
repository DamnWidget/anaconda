# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import logging

import jedi
from lib.anaconda_handler import AnacondaHandler
from jedi import refactoring as jedi_refactor
from commands import Doc, Goto, GotoAssignment, Rename, FindUsages
from commands import CompleteParameters, AutoComplete

logger = logging.getLogger('')


class JediHandler(AnacondaHandler):
    """Handle requests to execute Jedi related commands to the JsonServer

    The JsonServer instantiate an object of this class passing the method
    to execute as it came from the Sublime Text 3 Anaconda plugin
    """

    def run(self):
        """Call the specific method (override base class)
        """

        self.real_callback = self.callback
        self.callback = self.handle_result_and_purge_cache
        super(JediHandler, self).run()

    def handle_result_and_purge_cache(self, result):
        """Handle the result from the call and purge in memory jedi cache
        """

        try:
            jedi.cache.clear_time_caches()
        except:
            jedi.cache.clear_caches()
        self.real_callback(result)

    @property
    def script(self):
        """Generates a new valid Jedi Script and return it back
        """

        return self.jedi_script(**self.data)

    def jedi_script(
            self, source, line, offset, filename='', encoding='utf8', **kw):
        """Generate an usable Jedi Script
        """

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

    def goto_assignment(self):
        """Call goto_assignment
        """

        GotoAssignment(self.callback, self.uid, self.script)

    def doc(self, html=False):
        """Call doc
        """

        Doc(self.callback, self.uid, self.script, html)
