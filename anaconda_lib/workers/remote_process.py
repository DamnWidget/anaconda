
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details


class StubProcess(object):
    """Self descriptive class name, right?
    """

    def __init__(self, interpreter):
        self._process = None
        self._interpreter = None

    def start(self):
        """Just returns True and does nothing
        """

        return True
