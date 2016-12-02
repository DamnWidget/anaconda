
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

from ..anaconda_lib import aenum as enum


class WorkerStatus(enum.Enum):
    """Worker status unique enumeration
    """

    incomplete = 0
    healthy = 1
    faulty = 2
    quiting = 3
