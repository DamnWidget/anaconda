# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda is a python autocompletion and linting plugin for Sublime Text 3
"""

import os
import sys
import socket
import logging
import threading
import subprocess

import sublime
import sublime_plugin

from Anaconda.utils import get_settings
from Anaconda.anaconda_client import Client
from Anaconda.decorators import only_python, executor, enable_for_python

if sys.version_info < (3, 3):
    raise RuntimeError('Anaconda only works with Sublime Text 3')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.WARNING)

WORKERS = {}
WORKERS_LOCK = threading.RLock()


###############################################################################
# Anaconda Plugin Subclasses
###############################################################################
class AnacondaCompletionsListener(sublime_plugin.EventListener):
    """Jedi autocompletion for Sublime Text
    """

    completions = []

    @only_python
    def on_query_completions(self, view, prefix, locations):
        """Sublime Text autocompletion event handler
        """

        logger.info('Anaconda completion has been called')
        proposals = Worker.lookup(view).autocomplete(locations[0])

        if proposals:
            completion_flags = 0

            print(get_settings(view, 'suppress_word_completions'))
            if get_settings(view, 'suppress_word_completions', False):
                completion_flags = sublime.INHIBIT_WORD_COMPLETIONS

            if get_settings(view, 'suppress_explicit_completions', False):
                completion_flags |= sublime.INHIBIT_EXPLICIT_COMPLETIONS

            return (proposals, completion_flags)

        return proposals


class AnacondaGoto(sublime_plugin.TextCommand):
    """Jedi GoTo a Python defunition for Sublime Text
    """

    def run(self, edit):
        definitions = Worker.lookup(self.view).goto()
        if definitions:
            JediUsages(self).process(definitions)

    @enable_for_python
    def is_enabled(self):
        """Determine if this command is enabled or not
        """


class AnacondaFindUsages(sublime_plugin.TextCommand):
    """Jedi find usages for Sublime Text
    """

    def run(self, edit):
        JediUsages(self).process(Worker.lookup(self.view).usages(), True)

    @enable_for_python
    def is_enabled(self):
        """Determine if this command is enabled or not
        """


class AnacondaDoc(sublime_plugin.TextCommand):
    """Jedi get documentation string for Sublime Text
    """

    def run(self, edit):
        self.edit = edit
        doc = Worker.lookup(self.view).doc(self.view.sel()[0].begin())
        self.print_doc(doc)

    @enable_for_python
    def is_enabled(self):
        """Determine if this command is enabled or not
        """

    def print_doc(self, doc):
        """Print the documentation string into a Sublime Text panel
        """

        if doc is None:
            self.view.set_status(
                'anaconda_doc', 'Anaconda: No documentation found'
            )
            sublime.set_timeout_async(
                lambda: self.view.erase_status('anaconda_doc'), 5000
            )
        else:
            doc_panel = self.view.window().create_output_panel(
                'anaconda_documentation'
            )

            doc_panel.set_read_only(False)
            region = sublime.Region(0, doc_panel.size())
            doc_panel.erase(self.edit, region)
            doc_panel.insert(self.edit, 0, doc)
            doc_panel.set_read_only(True)
            doc_panel.show(0)
            self.view.window().run_command(
                'show_panel', {'panel': 'output.anaconda_documentation'}
            )


###############################################################################
# Classes
###############################################################################
class Worker:
    """Worker class for subprocess manipulation
    """

    def __init__(self, view):
        self.view = view
        self.client = None
        self.proccess = None
        self.restart()

    def restart(self):
        """Restart the server
        """

        self.proccess = self.start_worker(self)
        logger.info('starting anaconda server on port {}'.format(self.port))
        self.client = Client('localhost', self.port)

    def stop(self):
        """Stop any configured server for this Worker
        """

        if self.client is not None:
            self.client.close()
            self.client = None

        if self.proccess is not None:
            self.proccess.terminate()
            self.process = None

    @executor
    def autocomplete(self, location):
        """Call to autocomplete in the server
        """

        current_line, current_column = self.view.rowcol(location)
        data = self._prepare_data((current_line, current_column))

        result = self.client.request('autocomplete', **data)
        if result and result['success'] is True:
            return result['completions']

    @executor
    def run_linter(self, text, settings, filename):
        """Run the Linters in the server
        """

        data = {'code': text, 'settings': settings, 'filename': filename}
        result = self.client.request('run_linter', **data)
        if result and result['success'] is True:
            return result['errors']

    @executor
    def goto(self):
        """Call to goto in the server
        """

        current_line, current_column = self.view.rowcol(
            self.view.sel()[0].begin()
        )

        data = self._prepare_data((current_line, current_column))

        result = self.client.request('goto', **data)
        if result and result['success'] is True:
            return result['goto']

    @executor
    def usages(self):
        """Call to usages in the server
        """

        current_line, current_column = self.view.rowcol(
            self.view.sel()[0].begin()
        )
        data = self._prepare_data((current_line, current_column))

        result = self.client.request('usages', **data)
        if result and result['success'] is True:
            return result['usages']
        else:
            self.view.set_status('anaconda_doc', 'Anaconda: No usages found')
            sublime.set_timeout_async(
                lambda: self.view.erase_status('anaconda_doc'), 5000
            )
            return []

    @executor
    def doc(self, location):
        """Call to doc in the server
        """

        current_line, current_column = self.view.rowcol(location)
        if self.view.substr(location) in ['(', ')']:
            current_column -= 1

        data = self._prepare_data((current_line, current_column))
        result = self.client.request('doc', **data)
        if result and result['success'] is True:
            return result['doc']

    def _prepare_data(self, location):
        return {
            'source': self.view.substr(sublime.Region(0, self.view.size())),
            'line': location[0] + 1,
            'offset': location[1],
            'filename': self.view.file_name() or ''
        }

    @staticmethod
    def port():
        """Get a free port
        """

        s = socket.socket()
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()

        return port

    @staticmethod
    def lookup(view):
        """Lookup a Worker in the Workers stack
        """

        window = view.window()
        if window.window_id not in WORKERS:
            with WORKERS_LOCK:
                WORKERS[window.window_id] = Worker(view)

        return WORKERS[window.window_id]

    @staticmethod
    def generate_project_name(window):
        """
        Generates and returns back a valid project name for the window

        If there is not worker yet for this window, we create it and set a
        name for it. If we don't have a project file we just use the first
        folder name in the window's folders as name, if we don't have any
        folders in the window we just use the window.window_id
        """
        project_name = window.project_file_name()
        if project_name is None:
            folders = window.folders()
            if len(folders) > 0:
                project_name = window.folders()[0].rsplit(os.sep, 1)[1]
            else:
                project_name = 'anaconda-{id}'.format(id=window.window_id)
        else:
            project_name = project_name.rsplit(os.sep, 1)[1].split('.')[0]

        return project_name

    @staticmethod
    def start_worker(self):
        """Start a worker subprocess
        """

        self.port = Worker.port()
        window = self.view.window()
        project_name = Worker.generate_project_name(window)

        interp = get_settings(
            window.active_view(), 'python_interpreter', default='python'
        )
        extra_paths = get_settings(
            window.active_view(), 'extra_paths', default=''
        )

        kwargs = {
            'cwd': os.path.dirname(os.path.abspath(__file__)),
            'bufsize': -1
        }

        if sublime.platform() == 'windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kwargs['startupinfo'] = startupinfo

        WORKER_SCRIPT = os.path.join(
            os.path.dirname(__file__),
            'anaconda_server{}jsonserver.py'.format(os.sep)
        )

        sub_args = [
            interp, '-B', WORKER_SCRIPT, '-p', project_name, str(self.port)
        ]
        for extra_path in extra_paths.split(','):
            if extra_path != '':
                sub_args.extend(['-e', extra_path])
        sub_args.extend([str(os.getpid())])

        return subprocess.Popen(sub_args, **kwargs)


class JediUsages(object):
    """Work with Jedi definitions
    """

    def __init__(self, text):
        self.text = text

    def process(self, definitions, usages=False):
        """Process the definitions
        """

        if definitions is not None and len(definitions) == 1 and not usages:
            self._jump(*definitions[0])
        else:
            self._show_options(definitions, usages)

    def _jump(self, filename, lineno=None, columno=None):
        """Jump to a window
        """

        # process jumps from options window
        if type(filename) is int:
            if filename == -1:
                return

            filename, lineno, columno = self.options[filename]

        sublime.active_window().open_file(
            '{}:{}:{}'.format(filename, lineno or 0, columno or 0),
            sublime.ENCODED_POSITION
        )

    def _show_options(self, defs, usages):
        """Show a dropdown quickpanel with options to jump
        """

        if usages:
            options = [
                [o[0], 'line: {} column: {}'.format(o[1], o[2])] for o in defs
            ]
        else:
            options = defs[0]

        self.options = defs
        self.text.view.window().show_quick_panel(options, self._jump)
