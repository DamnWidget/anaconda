# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from commands import McCabe
from lib.anaconda_handler import AnacondaHandler
from linting.anaconda_mccabe import AnacondaMcCabe


class QAHandler(AnacondaHandler):
    """Handle request to execute quality assurance commands form the JsonServer
    """

    def mccabe(self, code, threshold, filename):
        """Return the McCabe code complexity errors
        """

        McCabe(
            self.callback, self.uid, self.vid, AnacondaMcCabe,
            code, threshold, filename
        )
