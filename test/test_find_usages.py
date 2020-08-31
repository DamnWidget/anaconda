
# Copyright (C) 2012-2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import jedi

from commands.find_usages import FindUsages
from handlers.jedi_handler import JediHandler

_code = 'from _usages_helper import usages_helper'


class TestFindUsages(object):
    """FindUsages tests suite
    """

    def test_find_usages_command(self):
        FindUsages(self._check_find_usages, 0, jedi.Script(_code))

    def test_find_usages_handler(self):
        data = {'source': _code, 'line': 1, 'offset': 40, 'filename': None}
        handler = JediHandler('usages', data, 0, 0, {}, self._check_find_usages)
        handler.run()

    def _check_find_usages(self, result):
        assert result['success'] is True
        assert len(result['result']) == 1
        assert result['result'][0] == ('_usages_helper.usages_helper', None, 1, 27)
        assert result['uid'] == 0
