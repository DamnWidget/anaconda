
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details


class Command(object):
    """Base class for every command that runs on Json Server
    """

    def __init__(self, callback, uid):
        self.uid = uid
        self.callback = callback

        self.run()


def get_function_parameters(call_def):
    """
    Return list function parameters, prepared for sublime completion.
    Tuple contains parameter name and default value
    """

    if not call_def:
        return []

    params = []
    for param in call_def.params:
        cleaned_param = param.description
        if '*' in cleaned_param or cleaned_param == 'self':
            continue

        params.append([s.strip() for s in cleaned_param.split('=')])

    return params
