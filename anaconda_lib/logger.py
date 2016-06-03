
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sys
import logging
import functools

import sublime

from .helpers import get_settings, active_view


def prevent_spam(func):
    """Prevent spamming in the logger
    """

    _last_messages = {}

    def _remove_from_cache(args):
        m = _last_messages.pop(args)
        if m == 1:
            return

        method = getattr(Log._logger, args[0])
        method(
            '{}\n ...last message repeated {} in the last 10s'.format(
                args[1], 'one more time' if m == 2 else '{} times'.format(m)
            )
        )

    @functools.wraps(func)
    def wrapper(cls, *args, **kwargs):
        if args in _last_messages:
            _last_messages[args] += 1
            return

        _last_messages[args] = 1
        sublime.set_timeout_async(lambda: _remove_from_cache(args), 10000)
        func(cls, args[0], *args[1:], **kwargs)

    return wrapper


class MetaLog(type):

    def __new__(cls, name, bases, attrs, **kwargs):
        log_level = get_settings(active_view(), 'log_level', 'info')
        if log_level not in ['debug', 'info', 'warning', 'error', 'fatal']:
            log_level = 'warning'

        cls._logger = logging.getLogger('anacondaST3')
        cls._logger.setLevel(logging.__getattribute__(log_level.upper()))
        log_handler = logging.StreamHandler(sys.stdout)
        log_handler.setFormatter(logging.Formatter(
            '%(name)s: %(levelname)s - %(message)s'
        ))

        cls._logger.addHandler(log_handler)
        cls._logger.propagate = False

        obj = super().__new__(cls, name, bases, attrs)
        for method in ['debug', 'info', 'warning', 'error', 'fatal']:
            setattr(obj, method, functools.partial(obj.write, method))

        return obj


class Log(metaclass=MetaLog):
    """The class is responsible to log errors
    """

    @classmethod
    @prevent_spam
    def write(cls, method, *args, **kwargs):
        """Info wrapper
        """

        f = getattr(cls._logger, method)
        f(*args, **kwargs)
