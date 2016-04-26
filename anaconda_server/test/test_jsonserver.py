
# Copyright (C) 2012 - 2016  Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""JsonServer related tests
"""

import unittest

from jsonserver import JSONHandler


class TestJsonServer(unittest.TestCase):
    """Convenience class to organize the tests
    """

    @classmethod
    def setupClass(cls):
        """Setup a JsonServer instance
        """

        cls.test_server = JSONHandler(('localhost', 9977))

    @classmethod
    def tearDown(cls):
        """Stop the JsonServer before exit
        """

        cls.test_server.shutdown()

    def test_collect_incoming_data(self):
        """Tests the incoming data collection
        """

        self.assertEqual(self.test_server.rbuffer, [])

