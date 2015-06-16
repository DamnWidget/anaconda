# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""Just a persistent list
"""

import os
import pickle
import logging


class PersistentList(list):

    """Just a persistent list
    """

    _file_path = os.path.join(
        os.path.dirname(__file__), os.pardir, '.disabled_views')

    def __init__(self):

        super(PersistentList, self).__init__()
        try:
            with open(self._file_path, 'rb') as fileobj:
                self.load(fileobj)
        except IOError:
            pass
        except Exception as e:
            logging.error(
                'Detected error {}, deleting persistent list...'.format(e))
            os.remove(self._file_path)

    def __setitem__(self, key, value):

        super(PersistentList, self).__setitem__(key, value)
        self.sync()

    def __delitem__(self, key):

        super(PersistentList, self).__delitem__(key)
        self.sync()

    def append(self, value):

        super(PersistentList, self).append(value)
        self.sync()

    def remove(self, value):

        super(PersistentList, self).remove(value)
        self.sync()

    def pop(self, index=None):

        if index is not None:
            value = super(PersistentList, self).pop(index)
        else:
            value = super(PersistentList, self).pop()

        self.sync()
        return value

    def sort(self, **kwargs):

        super(PersistentList, self).sort(**kwargs)
        self.sync()

    def load(self, fileobj):
        """Load the pickle contents
        """

        return self.extend(pickle.load(fileobj))

    def sync(self):
        """Write bytes and str elements of the list to the disk
        """

        with open(self._file_path, 'wb') as fileobj:
            l = [i for i in list(self) if type(i) is str or type(i) is bytes]
            return pickle.dump(l, fileobj, 2)
