
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import inspect

from .compat import AnacondaHandlerProvider


class AnacondaHandler(AnacondaHandlerProvider):
    """All anaconda handlers should inherit from this class

    The constructor method pass a command (that is a string representation
    of the command to invoque) and we call the super class method
    `_register_command` so super classes of this class *must* implement
    that method.

    If you need to overrie the constructor in an specific handler, make sure
    that you call the base class constructor with:

        super(HandlerName, self).__init__(command, data, uid)
    """

    def __init__(self, command, data, uid, vid, settings, callback, debug=False):
        self.uid = uid
        self.vid = vid
        self.data = data
        self.debug = debug
        self.callback = callback
        self.command = command
        self.settings = settings

    def run(self):
        """Call the specific method
        """
        command = getattr(self, self.command)
        try:
            func_code = command.func_code
        except AttributeError:
            # Renamed in Python 3
            func_code = command.__code__

        # Loop through self.data, pulling out the parameters specified in the command
        kwargs = {}
        for argument, value in self.data.items():
            if argument in inspect.getargs(func_code).args:
                kwargs[argument] = value

        command(**kwargs)

    @classmethod
    def get_handler(cls, handler_type):
        """Return the given handler type if registered
        """
        return cls._registry.get(handler_type)
