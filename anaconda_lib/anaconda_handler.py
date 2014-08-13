# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import inspect


class AnacondaHandler(object):
    """All anaconda handlers should inherit from this class

    The constructor method pass a command (that is a string representation
    of the command to invoque) and we call the super class method
    `_register_command` so super classes of this class *must* implement
    that method.

    If you need to overrie the constructor in an specific handler, make sure
    that you call the base class constructor with:

        super(HandlerName, self).__init__(command, data, uid)
    """

    def __init__(self, command, data, uid, vid, callback, debug=False):
        self.uid = uid
        self.vid = vid
        self.data = data
        self.debug = debug
        self.callback = callback
        self.command = command

    def run(self):
        """Call the specific method
        """

        command = getattr(self, self.command)
        kwargs = {}
        for argument, value in self.data.items():
            if argument in inspect.getargs(command.func_code).args:
                kwargs[argument] = value

        self.callback(command(**kwargs))
