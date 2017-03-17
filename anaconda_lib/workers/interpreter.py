
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import socket

from urllib.parse import urlparse, parse_qs

import sublime

from ..logger import Log
from ..unix_socket import UnixSocketPath
from ..helpers import project_name, debug_enabled
from ..helpers import get_settings, active_view, get_interpreter
from ..vagrant import VagrantIPAddressGlobal, VagrantMachineGlobalInfo


class Interpreter(object):
    """Parses a configured Python Interpreter
    """

    def __init__(self, interpreter_string):
        self.__data = {}
        self.__raw_interpreter = interpreter_string
        self.__parse_raw_interpreter()
        self.__project_name = ''

    def __getattr__(self, attr_name):
        """Return data as it was part of the object itself
        """

        return self.__data.get(attr_name, None)

    @property
    def raw_interpreter(self):
        return self.__raw_interpreter

    @property
    def for_local(self):
        """Returns True if this interpreter is configured for local
        """

        return self.scheme == 'local'

    @property
    def for_remote(self):
        """Return True if this interpreter is configured for remote
        """

        return self.scheme == 'tcp'

    @property
    def for_vagrant(self):
        """Return True if this interpreter is configured for vagrant
        """

        return self.scheme == 'vagrant'

    @property
    def project_name(self):
        """Set project name if necessary and return it back
        """

        if not self.__project_name:
            self.__project_name = project_name()

        return self.__project_name

    def renew_interpreter(self):
        """Renew the whole intrepreter
        """

        if not self.for_local:
            return

        self.__prepare_local_interpreter()

    def __prepare_local_interpreter(self):
        """Prepare data for the local interpreter if scheme is lcoal
        """

        view = active_view()
        self.__extract_port(view)
        self.__extract_paths(view)
        self.__extract_python_interpreter(view)
        self.__extract_script()

        args = [self.python, '-B', self.script_file, '-p', self.project_name]
        if self.port is not None:
            args.append(str(self.port))
        if len(self.paths) > 0:
            paths = [p for p in self.paths if os.path.exists(p)]
            args.extend(['-e', ','.join(paths)])
        args.extend([str(os.getpid())])

        kwargs = {}
        folders = sublime.active_window().folders()
        if len(folders) > 0 and os.path.exists(folders[0]):
            kwargs['cwd'] = folders[0]

        self.__data['arguments'] = (args, kwargs)

    def __extract_port(self, view):
        """Extract the port to connect to
        """

        if sublime.platform() != 'linux':
            self.__data['host'] = 'localhost'
        else:
            self.__data['host'] = self.__get_unix_domain_socket()
            return

        if debug_enabled(view):
            port = get_settings(view, 'jsonserver_debug_port', 9999)
            self.__data['port'] = port
            return

        if sublime.platform() != 'linux':
            s = socket.socket()
            s.bind(('', 0))
            self.__data['port'] = s.getsockname()[1]
            s.close()

    def __extract_paths(self, view):
        """Extract a list of paths to be added to jedi
        """

        extra = get_settings(view, 'extra_paths', [])
        paths = [os.path.expanduser(os.path.expandvars(p)) for p in extra]

        try:
            paths.extend(sublime.active_window().folders())
        except AttributeError:
            Log.warning(
                'Your `extra_paths` configuration is a string but we are '
                'expecting a list of strings.'
            )
            paths = paths.split(',')
            paths.extend(sublime.active_window().folder())

        self.__data['paths'] = paths

    def __extract_python_interpreter(self, view):
        """Extract the configured python interpreter
        """

        try:
            python = os.path.expanduser(
                os.path.expandvars(get_interpreter(view))
            )
            if '$VIRTUAL_ENV' in python:
                Log.warning(
                    'WARNING: your anaconda configured python interpreter '
                    'is {} but there is no $VIRTUAL_ENV key in your '
                    'environment, falling back to `python`'.format(python)
                )
        except:
            python = 'python'
        finally:
            self.__data['python'] = python

    def __extract_script(self):
        """Extrct the jsonserver.py script location
        """

        self.__data['script_file'] = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'anaconda_server', 'jsonserver.py'
        )

    def __get_unix_domain_socket(self):
        """Compound the Unix domain socket path
        """

        if sublime.platform() != 'linux':
            return 'localhost'

        return UnixSocketPath(self.project_name).socket

    def __parse_raw_interpreter(self):
        """Parses the raw interpreter string for later simple use
        """

        urldata = urlparse(self.__raw_interpreter)
        self.__data['scheme'] = urldata.scheme if urldata.scheme else 'local'
        if len(self.__data['scheme']) == 1:
            self.__data['scheme'] = 'local'

        if self.for_local:
            # we are set up for local return now and do our thing
            return self.__prepare_local_interpreter()

        if urldata.query and 'manual=' in urldata.query:
            self.__data['scheme'] = 'tcp'

        netloc = urldata.netloc
        if '@' in urldata.netloc:
            left, netloc = netloc.split('@')
            self.__data['username'], self.__data['password'] = left.split(':')

        if self.for_remote:
            self.__data['host'], self.__data['port'] = netloc.split(':')

        if self.for_vagrant:
            self.__data['machine'], self.__data['port'] = netloc.split(':')

        if urldata.query:
            options = parse_qs(urldata.query)
            for key, value in options.items():
                self.__data[key] = (
                    value if key in ['extra', 'pathmap'] else value[0]
                )

        if self.for_vagrant:
            self.__data['network'] = self.__data.get('network', 'forwarded')
            self.__data['interpreter'] = (
                self.__data.get('interpreter', 'python')
            )
            _vagrant_hosts = {
                'forwarded': 'localhost',
                'private': self.address,
                'public': VagrantIPAddressGlobal(
                    VagrantMachineGlobalInfo(self.machine).machine_id, self.dev
                ).ip_address
            }
            self.__data['host'] = _vagrant_hosts[self.network]

        pathmap = {}
        for map_data in self.__data.get('pathmap', []):
            split_data = map_data.split(',')
            if len(split_data) != 2:
                Log.warning('pathmap corruption? -> {}'.format(map_data))
                continue

            local_path = os.path.expanduser(os.path.expandvars(split_data[0]))
            remote_path = os.path.expanduser(os.path.expandvars(split_data[1]))
            pathmap[local_path] = remote_path

        self.__data['pathmap'] = pathmap

    def __repr__(self):
        """String representation
        """

        try:
            return ' '.join(self.arguments[0])
        except TypeError:
            rep = ''
            for k, v in self.__data.items():
                rep + k + ': ' + v + '\n'
            return rep
