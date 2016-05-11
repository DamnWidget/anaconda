
# Copyright (C) 2012-2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from commands.mccabe import McCabe
from handlers.qa_handler import QAHandler
from linting.anaconda_mccabe import AnacondaMcCabe


class TestQa(object):
    """QA test suite
    """

    _code = '''
def f(n):
    if n > 3:
        return "bigger than three"
    elif n > 4:
        return "is never executed"
    else:
        return "smaller than or equal to three"
    '''

    def test_mccabe_command(self):
        McCabe(
            self._check_mccabe, 0, 0, AnacondaMcCabe, self._code, 0, '')

    def test_mccabe_high_threshold(self):

        def _check_threshold_4(result):
            assert result['success'] is True
            assert len(result['errors']) == 1

        def _check_threshold_7(result):
            assert result['success'] is True
            assert len(result['errors']) == 0

        McCabe(_check_threshold_4, 0, 0, AnacondaMcCabe, self._code, 4, '')
        McCabe(_check_threshold_7, 0, 0, AnacondaMcCabe, self._code, 7, '')

    def test_mccabe_handler(self):
        data = {'code': self._code, 'threshold': 4, 'filename': ''}
        handler = QAHandler('mccabe', data, 0, 0, self._check_mccabe)
        handler.run()

    def _check_mccabe(self, result):
        assert result['success'] is True
        assert result['uid'] == 0
        assert result['vid'] == 0
        assert len(result['errors']) == 1
        assert result['errors'][0]['message'] == "'f' is too complex (4)"
        assert result['errors'][0]['line'] == 2
        assert result['errors'][0]['code'] == 'C901'
        assert result['errors'][0]['offset'] == 1
