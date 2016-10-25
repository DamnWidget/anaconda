
# Copyright (C) 2012-2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import re
import sys

import jedi

from commands.goto import Goto, GotoAssignment
from handlers.jedi_handler import JediHandler

src = 'import re; re.compile'
PYTHON3 = sys.version_info >= (3, 0)


class TestGoto(object):
    """Goto test suite
    """

    def test_goto_command(self):
        Goto(self._check_goto, 0, jedi.Script(src))

    def test_goto_handler(self):
        data = {'source': src, 'line': 1, 'offset': 21}
        handler = JediHandler('goto', data, 0, 0, self._check_goto)
        handler.run()

    def _check_goto(self, result):
        assert result['success'] is True
        assert len(result['result']) == 1
        if PYTHON3:
            assert result['result'][0][1] == re.__file__
        else:
            file_name = re.__file__
            if '.pyc' in file_name:
                assert result['result'][0][1] == file_name[:-1]
            else:
                assert result['result'][0][1] == file_name


class TestGotoAssignment(object):
    """Goto test suite
    """

    def test_goto_assignment_command(self):
        GotoAssignment(self._check_goto_assignment, 0, jedi.Script(src, line=1, column=13))

    def test_goto_assignment_handler(self):
        data = {'source': src, 'line': 1, 'offset': 13}
        handler = JediHandler('goto_assignment', data, 0, 0, self._check_goto_assignment)
        handler.run()

    def _check_goto_assignment(self, result):
        assert result['success'] is True
        assert len(result['result']) == 1
        result = result['result'][0]
        assert result[1] is None
        assert result[2] == 1
        assert result[3] == 8
