# -*- coding: utf8 -*-

# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""Minimalist Callbacks implementation based on @NorthIsUp pull request
"""

import sys
import uuid
import logging
from threading import RLock
from functools import partial

import sublime

from ..anaconda_lib import aenum as enum
from ._typing import Callable, Any, Union

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


@enum.unique
class CallbackStatus(enum.Enum):
    """Callback status unique enumeration
    """

    unfired = 'unfired'
    succeeded = 'succeeded'
    failed = 'failed'
    timed_out = 'timed_out'


class Callback(object):
    """This class implements an error safe non retriable callbacks mechanism

    Instances of this class can be passed as callbacks to Anaconda's
    asynchronous client methods.

    You can pass callback methods for success, error or timeout using the
    constructor parameters `on_success`, `on_failure` and `on_timeout` or
    you can just call the `on` method. Take into account that if the timeout
    value is set to 0 (or less), the timeout callback will never be called.

    .. note::

        A callback object can be called only once, try to call it more than
        once should result in a RuntimeError raising
    """

    def __init__(self, on_success: Callable=None, on_failure: Callable=None, on_timeout: Callable=None, timeout: Union[int, float]=0) -> None:  # noqa
        self._lock = RLock()
        self._timeout = 0  # type: Union[int, float]
        self.uid = uuid.uuid4()  # type: uuid.UUID
        self.waiting_for_timeout = False
        self._status = CallbackStatus.unfired  # type: enum.Enum
        self.callbacks = {'succeeded': on_success, 'failed': on_failure}  # type: Dict[str, Callable]  # noqa
        if on_timeout is not None and callable(on_timeout):
            self.callbacks['timed_out'] = on_timeout

        self.timeout = timeout
        if on_timeout is not None and timeout > 0:
            self.initialize_timeout()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """This is called directly form the JSONClient when receive a message
        """

        with self._lock:
            self._infere_status_from_data(*args, **kwargs)
            return self._fire_callback(*args, **kwargs)

    @property
    def id(self) -> uuid.UUID:
        """Return back the callback id
        """
        return self.uid

    @property
    def hexid(self) -> str:
        """Return back the callback hexadecimal id
        """
        return self.uid.hex

    @property
    def timeout(self):
        """Return back the callback timeout
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value: Union[int, float]) -> None:
        """Set the timeout, take sure its an interger or float value
        """

        if not isinstance(value, (int, float)):
            raise RuntimeError('Callback.timeout must be integer or float!')

        self._timeout = value

    @property
    def status(self) -> enum.Enum:
        """Return the callback status
        """
        return self.status

    @status.setter
    def status(self, status: CallbackStatus) -> None:
        """Set the callback status, it can be set only once.

        This function is Thread Safe

        :param status: it can be a CallbackStatus property or an string with
            one of the valid status values; succeeded, failed, timed_out
        """

        with self._lock:
            if self._status != CallbackStatus.unfired:
                if self._status != CallbackStatus.timed_out:
                    raise RuntimeError(
                        'Callback {} already fired!'.format(self.hexid)
                    )
                else:
                    logger.info(
                        'Calback {} came back with data but it\'s status '
                        'was `timed_out` already'.format(self.hexid)
                    )
                    return

            if isinstance(status, CallbackStatus):
                self._status = status
            else:
                status = CallbackStatus._member_map_.get(status)
                if status is not None:
                    self._status = status
                else:
                    raise RuntimeError(
                        'Status {} does not exists!'.format(status)
                    )

    def initialize_timeout(self) -> None:
        """Initialize the timeouts if any
        """

        def _timeout_callback(*args: Any, **kwargs: Any) -> None:
            """Defualt timeout callback dummy method, can be overriden
            """
            raise RuntimeError('Timeout occurred on {}'.format(self.hexid))

        def _on_timeout(func: Callable, *args: Any, **kwargs: Any) -> None:
            """We need this wrapper to don't call timeout by accident
            """
            if self._status is CallbackStatus.unfired:
                self.status = CallbackStatus.timed_out
                func(*args, **kwargs)

        if self.timeout > 0:
            self.waiting_for_timeout = True
            callback = self.callbacks.get('timed_out', _timeout_callback)
            sublime.set_timeout(
                partial(_on_timeout, callback), self.timeout * 1000
            )

    def on(self, success: Callable=None, error: Callable=None, timeout: Callable=None) -> None:  # noqa
        """Another (more semantic) way to initialize the callback object
        """

        if success is not None and self.callbacks.get('succeeded') is None:
            self.callbacks['succeeded'] = success

        if error is not None and self.callbacks.get('failed') is None:
            self.callbacks['failed'] = error

        if timeout is not None and self.callbacks.get('timed_out') is None:
            if callable(timeout):
                self.callbacks['timed_out'] = timeout
                self.initialize_timeout()

    def _infere_status_from_data(self, *args: Any, **kwargs: Any) -> None:
        """
        Set the status based on extracting a code from the callback data.
        Supports two protocols checked in the followin order:

        1) data = {'status': 'succeeded|failed|timed_out'}
        2) data = {'success': True|False}   <- back compatibility
        """

        data = kwargs.get('data') or args[0] if args else {}
        if 'status' in data:
            self.status = data['status']
        elif 'success' in data:
            smap = {True: 'succeeded', False: 'failed'}
            self.status = smap[data['success']]
        else:
            self.status = 'succeeded'  # almost safe, trust me

    def _fire_callback(self, *args: Any, **kwargs: Any) -> Any:
        """Fire the right calback based on the status
        """

        def _panic(*args: Any, **kwargs: Any) -> None:
            """Just called on panic situations
            """

            if self.status is CallbackStatus.failed:
                callback = self.callbacks.get('succeeded')
                if callback is not None:
                    return callback(*args, **kwargs)

            raise RuntimeError(
                'We tried to call non existing callback {}!'.format(
                    self.status.value
                )
            )

        callback = self.callbacks.get(self._status.value, _panic)
        return callback and callback(*args, **kwargs)
