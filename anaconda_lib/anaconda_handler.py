# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details


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
        self.data = data
        self.debug = debug
        self.callback = callback
        self._register_command(command)

    def __call__(self):
        """Call the specific method
        """

        command = getattr(self, self.command['method'])
        command(self.uid, **self.command['kwargs'])

    def _register_command(self, command):
        """Register a command in the handler

        If you need to override this method in an specific handler, make
        sure to call the base class `_register_command`
        """

        kwargs = {}
        if 'settings' in self.data:
            kwargs['settings'] = self.data.pop('settings')

        self.command = {'method': command, 'kwargs': kwargs}
