
# Copyright (C) 2012-2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from commands.autoformat import AutoPep8
from handlers.autoformat_handler import AutoFormatHandler

_code = '''import math, sys;

def example1():
    ####This is a long comment. This should be wrapped to fit within 72 characters.
    some_tuple=(   1,2, 3,'a'  );
    some_variable={'long':'Long code lines should be wrapped within 79 characters.',
    'other':[math.pi, 100,200,300,9876543210,'This is a long string that goes on'],
    'more':{'inner':'This whole logical line should be wrapped.',some_tuple:[1,
    20,300,40000,500000000,60000000000000000]}}
    return (some_tuple, some_variable)
def example2(): return {'has_key() is deprecated':True}.has_key({'f':2}.has_key(''));
class Example3(   object ):
    def __init__    ( self, bar ):
     #Comments should have a space after the hash.
     if bar : bar+=1;  bar=bar* bar   ; return bar
     else:
                    some_string = """
                       Indentation in multiline strings should not be touched.
Only actual code should be reindented.
"""
                    return (sys.path, some_string)'''

_fixed_code_select = '''import math, sys;

def example1():
    # This is a long comment. This should be wrapped to fit within 72
    # characters.
    some_tuple=(   1,2, 3,'a'  );
    some_variable={
    'long':'Long code lines should be wrapped within 79 characters.',
    'other':[
        math.pi,
        100,
        200,
        300,
        9876543210,
        'This is a long string that goes on'],
        'more':{
            'inner':'This whole logical line should be wrapped.',
            some_tuple:[
                1,
                20,
                300,
                40000,
                500000000,
                60000000000000000]}}
    return (some_tuple, some_variable)
def example2(): return {'has_key() is deprecated':True}.has_key(
    {'f':2}.has_key(''));
class Example3(   object ):
    def __init__    ( self, bar ):
     #Comments should have a space after the hash.
     if bar : bar+=1;  bar=bar* bar   ; return bar
     else:
                    some_string = """
                       Indentation in multiline strings should not be touched.
Only actual code should be reindented.
"""
                    return (sys.path, some_string)
'''

_fixed_code = '''import math
import sys


def example1():
    # This is a long comment. This should be wrapped to fit within 72
    # characters.
    some_tuple = (1, 2, 3, 'a')
    some_variable = {
        'long': 'Long code lines should be wrapped within 79 characters.',
        'other': [
            math.pi,
            100,
            200,
            300,
            9876543210,
            'This is a long string that goes on'],
        'more': {
            'inner': 'This whole logical line should be wrapped.',
            some_tuple: [
                1,
                20,
                300,
                40000,
                500000000,
                60000000000000000]}}
    return (some_tuple, some_variable)


def example2(): return ('' in {'f': 2}) in {'has_key() is deprecated': True}


class Example3(object):

    def __init__(self, bar):
        # Comments should have a space after the hash.
        if bar:
            bar += 1
            bar = bar * bar
            return bar
        else:
            some_string = """
                       Indentation in multiline strings should not be touched.
Only actual code should be reindented.
"""
            return (sys.path, some_string)
'''


class TestAutoformat(object):
    """AutoPEP8 formatting tests suite
    """

    def setUp(self):
        self.settings = {
            'aggressive': 2,
            'list-fixes': False,
            'autoformat_ignore': [],
            'autoformat_select': [],
            'pep8_max_line_length': 79
        }

    def test_autoformat_command(self):
        AutoPep8(self._check_autoformat, 0, 0, _code, self.settings)

    def test_autoformat_ignore(self):
        self.settings['autoformat_ignore'] = ['E501']
        AutoPep8(self._check_max_line, 0, 0, _code, self.settings)

    def test_autoformat_select(self):
        self.settings['autoformat_select'] = ['E501']
        AutoPep8(self._check_autoformat_select, 0, 0, _code, self.settings)

    def test_autoformat_max_line_length(self):
        self.settings['pep8_max_line_length'] = 120
        AutoPep8(self._check_max_line, 0, 0, _code, self.settings)

    def test_autoformat_handler(self):
        data = {'code': _code, 'settings': self.settings}
        handler = AutoFormatHandler('pep8', data, 0, 0, self._check_autoformat)  # noqa
        handler.run()

    def _check_autoformat(self, result):
        assert result['success'] is True
        assert result['buffer'] == _fixed_code
        assert result['uid'] == 0
        assert result['vid'] == 0

    def _check_autoformat_select(self, result):
        assert result['success'] is True
        assert result['buffer'] == _fixed_code_select
        assert result['uid'] == 0
        assert result['vid'] == 0

    def _check_max_line(self, result):
        assert result['success'] is True
        assert result['buffer'].splitlines()[5] == '    # This is a long comment. This should be wrapped to fit within 72 characters.'  # noqa
        assert result['uid'] == 0
        assert result['vid'] == 0

