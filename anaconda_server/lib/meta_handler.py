
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from .registry import HandlerRegistry


class AnacondaHandlerMeta(type):
    """Register new anaconda handlers
    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_registry'):
            cls._registry = HandlerRegistry()

        if hasattr(cls, '__handler_type__'):
            cls._registry.register(cls)
