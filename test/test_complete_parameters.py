
# Copyright (C) 2012-2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sys

import jedi

from handlers.jedi_handler import JediHandler
from commands.complete_parameters import CompleteParameters

PYTHON3 = sys.version_info >= (3, 0)


class TestCompleteParameters(object):
    """CompleteParameters tests suite
    """

    def setUp(self):
        self.settings = {'complete_all_parameters': False}
        self.script = jedi.Script('import json; json.loads(')

    def test_complete_parameters_command(self):
        CompleteParameters(
            self._check_parameters, 0, self.script, self.settings)

    def test_complete_all_parameters(self):
        self.settings['complete_all_parameters'] = True
        CompleteParameters(
            self._check_all_parameters, 0, self.script, self.settings)

    def test_complete_parameters_handler(self):
        data = {
            'source': 'import json; json.loads(', 'line': 1,
            'offset': 24, 'filname': None, 'settings': self.settings
        }
        handler = JediHandler(
            'parameters', data, 0, 0, self._check_parameters)
        handler.run()

    def test_complete_all_parameters_handler(self):
        self.settings['complete_all_parameters'] = True
        data = {
            'source': 'import json; json.loads(', 'line': 1,
            'offset': 24, 'filname': None, 'settings': self.settings
        }
        handler = JediHandler(
            'parameters', data, 0, 0, self._check_all_parameters)
        handler.run()

    def _check_parameters(self, result):
        assert result['success'] is True
        assert result['template'] == '${1:s}' if PYTHON3 else u'${1:s}'
        assert result['uid'] == 0

    def _check_all_parameters(self, result):
        assert result['success'] is True
        assert result['template'] == "${1:s}, encoding=${2:None}, cls=${3:None}, object_hook=${4:None}, parse_float=${5:None}, parse_int=${6:None}, parse_constant=${7:None}, object_pairs_hook=${8:None}"  # noqa
        assert result['uid'] == 0
