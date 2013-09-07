
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""Package Control progress bar like
"""

import time
import threading

import sublime


class ProgressBar(threading.Thread):
    """A progress bar animation that runs in other thread
    """

    def __init__(self, messages):
        threading.Thread.__init__(self)
        self.messages = messages
        self.die = False

    def run(self):
        """Just run the thread
        """

        i = 0
        size = 8
        addition = 1
        while not self.die:

            pos = i % size
            status = '{}={}'.format(' ' * pos, ' ' * ((size - 1) - pos))

            sublime.status_message('{} [{}]'.format(
                self.messages['start'], status)
            )

            if not (size - 1) - pos:
                addition = -1
            if not pos:
                addition = 1

            i += addition
            time.sleep(0.1)

        sublime.status_message(self.messages['end'])

    def terminate(self):
        """Terminate the thread
        """

        self.die = True
