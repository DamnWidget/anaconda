
# Copyright (C) 2012-2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sys
sys.path.insert(0, '../anaconda_server')

import shlex
from subprocess import Popen, PIPE


class TestJsonServer(object):
    """Simple JsonServer test class
    """

    @classmethod
    def setUpClass(cls):
        """Prepare the test server
        """

        cls.server = Popen(shlex.split(
            '{0} -B ../anaconda_server/jsonserver.py -p test 9999 DEBUG'.format(sys.executable)  # noqa
        ), stdout=PIPE, stderr=PIPE)
        cls.server_out, cls.server_err = cls.server.communicate()

    def tearDonwClass(cls):
        """Just shutdown the server
        """

        cls.server.terminate()

    def test_pollas(self):
        """Test pollas
        """

        assert True
