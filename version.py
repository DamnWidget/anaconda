
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os

messages_json = os.path.join(os.path.dirname(__file__), 'messages.json')
with open(messages_json, 'r') as message_file:
    message_data = message_file.read()

ver = message_data.splitlines()[-2].split(':')[0].strip().replace('"', '')
version = tuple([int(i) for i in ver.split('.')])
