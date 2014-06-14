# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
This file is a wrapper for autopep8 library.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../linting'))
import threading

from .autopep8_lib import autopep8


class AnacondaAutopep8(threading.Thread):

    """Wrapper class around native autopep8 implementation
    """

    def __init__(self, settings, code, callback):
        threading.Thread.__init__(self)
        self.code = code
        self.callback = callback
        self.options, _ = autopep8.parse_args(self.parse_settings(settings))

    def run(self):
        self.callback(autopep8.fix_string(self.code, options=self.options))

    def parse_settings(self, settings):
        """Map anaconda settings to autopep8 settings
        """

        args = []
        args += ['-a'] * settings.get('aggressive', 0)

        if len(settings.get('autoformat_ignore', [])) > 0:
            args += ['--ignore={}'.format(
                ','.join(settings.get('autoformat_ignore')))]

        if len(settings.get('autoformat_select', [])) > 0:
            args += ['--select={}'.format(
                ','.join(settings.get('autoformat_select')))]

        args += ['--max-line-length={}'.format(
            settings.get('pep8_max_line_length', 79))]
        args += ['anaconda_rocks']

        return args
