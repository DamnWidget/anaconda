
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details


class Repr(type):
    """Metaclass to define __repr__ for class instead of instance
    """

    def __repr__(cls):
        if hasattr(cls, '_repr'):
            return getattr(cls, '_repr')()

        return super(Repr, cls).__repr__()
