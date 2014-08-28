
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import sys
import logging


class HandlerRegistry(object):
    """Register anaconda JsonServer handlers
    """

    initialized = False

    def __init__(self):
        self._handlers = {}

    def initialize(self):
        """Load handlers from anaconda installed plugins
        """

        if self.initialized:
            return

        self._import_plugin_handlers()
        self.initialized = True

    def get(self, handler_type):
        """Retrieve the given handler type or none
        """

        return self._handlers.get(handler_type)

    def register(self, handler):
        """Register a new handler
        """

        self._handlers[handler.__handler_type__] = handler

    def _import_plugin_handlers(self):
        """Import hadnlers from anaconda plugins
        """

        path = os.path.join(os.path.dirname(__file__), '../../../')
        packages = [
            os.path.join(path, f) for f in os.listdir(path)
            if f.startswith('anaconda_')
        ]
        for package in packages:
            if 'vagrant' in package or not os.path.isdir(package):
                continue

            lang = package.rsplit('anaconda_', 1)[1]
            sys.path.append('{}/plugin'.format(package))
            mod_name = 'handlers_{}'.format(lang)
            mod = __import__(mod_name, globals(), locals())
            logging.info(
                '[anaconda_plugins] imported handlers for {}'.format(mod)
            )
