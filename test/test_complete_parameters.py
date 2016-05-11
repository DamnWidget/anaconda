
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
        self.script = jedi.Script('open(')

    def test_complete_parameters_command(self):
        CompleteParameters(
            self._check_parameters, 0, self.script, self.settings)

    def test_complete_all_parameters(self):
        self.settings['complete_all_parameters'] = True
        CompleteParameters(
            self._check_all_parameters, 0, self.script, self.settings)

    def test_complete_parameters_handler(self):
        data = {
            'source': 'open(', 'line': 1,
            'offset': 5, 'filname': None, 'settings': self.settings
        }
        handler = JediHandler(
            'parameters', data, 0, 0, self._check_parameters)
        handler.run()

    def test_complete_all_parameters_handler(self):
        self.settings['complete_all_parameters'] = True
        data = {
            'source': 'open(', 'line': 1,
            'offset': 5, 'filname': None, 'settings': self.settings
        }
        handler = JediHandler(
            'parameters', data, 0, 0, self._check_all_parameters)
        handler.run()

    def _check_parameters(self, result):
        assert result['success'] is True
        assert result['template'] == '${1:file}' if PYTHON3 else u'${1:file}'
        assert result['uid'] == 0

    def _check_all_parameters(self, result):
        assert result['success'] is True
        assert result['template'] == "${1:file}, mode=${2:'r'}, buffering=${3:-1}, encoding=${4:None}, errors=${5:None}, newline=${6:None}, closefd=${7:True}" if PYTHON3 else u"${1:file}, mode=${2:'r'}, buffering=${3:-1}, encoding=${4:None}, errors=${5:None}, newline=${6:None}, closefd=${7:True}"  # noqa
        assert result['uid'] == 0
