
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""Package Control progress bar like
"""

import threading

import sublime


class ProgressBar(threading.Thread):
    """A progress bar animation that runs in other thread
    """

    class Status(object):
        NONE = None
        SUCCESS = 'end'
        FAILURE = 'fail'
        TIMEOUT = 'timeout'

    def __init__(self, messages):
        threading.Thread.__init__(self)
        self.messages = messages
        self.addition = 1
        self.die = False

    def run(self):
        """Just run the thread
        """

        sublime.set_timeout(lambda: self.update(0), 100)

    def update(self, i):
        """Update the progress bar
        """

        if self.die:
            return

        size = 8
        pos = i % size
        status = '{}={}'.format(' ' * pos, ' ' * ((size - 1) - pos))

        sublime.status_message('{} [{}]'.format(
            self.messages['start'], status)
        )

        if not (size - 1) - pos:
            self.addition = -1
        if not pos:
            self.addition = 1

        i += self.addition

        sublime.set_timeout_async(lambda: self.update(i), 100)

    def terminate(self, status=None):
        """Terminate this thread
        """
        status = status or self.Status.SUCCESS

        message = self.messages.get(status) or self.messages[self.Status.SUCCESS]  # noqa
        sublime.status_message(message)
        self.die = True
