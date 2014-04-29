# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
This file is a wrapper for autopep8 library.
"""

import logging
import traceback

from .base import Command
from autopep.autopep8_lib import autopep8


class AutoPep8(Command):
    """Run autopep8 in the given file
    """

    def __init__(self, callback, uid, vid, code, settings):
        self.vid = vid
        self.code = code
        self.options, _ = autopep8.parse_args(self.parse_settings(settings))
        super(AutoPep8, self).__init__(callback, uid)

    def run(self):
        """Run the command
        """

        try:
            self.callback({
                'success': True,
                'buffer': autopep8.fix_lines(
                    self.code.splitlines(), options=self.options),
                'uid': self.uid,
                'vid': self.vid
            })
        except Exception as error:
            logging.error(str(error))
            print(traceback.format_exc().splitlines())
            logging.debug(traceback.format_exc().splitlines())
            self.callback({
                'success': False,
                'error': str(error),
                'uid': self.uid,
                'vid': self.vid
            })

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
