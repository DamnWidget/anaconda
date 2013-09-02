# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda is a python autocompletion and linting plugin for Sublime Text 3
"""

import os
import sys
import time
import logging
import traceback
from string import Template

from functools import partial

import sublime
import sublime_plugin

from .anaconda_lib import autopep
from .anaconda_lib.worker import Worker
from .anaconda_lib.jediusages import JediUsages
from .anaconda_lib.progress_bar import ProgressBar
from .anaconda_lib.helpers import get_settings, active_view, prepare_send_data
from .anaconda_lib.decorators import (
    only_python, enable_for_python, profile, is_python,
    on_auto_formatting_enabled
)


if sys.version_info < (3, 3):
    raise RuntimeError('Anaconda only works with Sublime Text 3')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

JUST_COMPLETED = False


class AnacondaEventListener(sublime_plugin.EventListener):
    """Anaconda events listener class
    """

    completions = []
    ready_from_defer = False

    @only_python
    @profile
    def on_query_completions(self, view, prefix, locations):
        """Sublime Text autocompletion event handler
        """

        global JUST_COMPLETED

        if self.ready_from_defer is True:
            completion_flags = 0

            if get_settings(view, 'suppress_word_completions', False):
                completion_flags = sublime.INHIBIT_WORD_COMPLETIONS

            if get_settings(view, 'suppress_explicit_completions', False):
                completion_flags |= sublime.INHIBIT_EXPLICIT_COMPLETIONS

            cpl = self.completions
            self.completions = []
            self.ready_from_defer = False
            JUST_COMPLETED = True

            return (cpl, completion_flags)

        location = view.rowcol(locations[0])
        data = prepare_send_data(location, 'autocomplete')

        Worker().execute(self._complete, **data)
        return

    @only_python
    @on_auto_formatting_enabled
    def on_pre_save_async(self, view):
        """Called just before the file is going to be saved
        """

        view.run_command('anaconda_auto_format')

    @only_python
    def on_modified_async(self, view):
        """Called after changes has been made to a view.
        """
        global JUST_COMPLETED

        if (view.substr(view.sel()[0].begin() - 1) == '('
                and view.substr(view.sel()[0].begin()) == ')'):
            if JUST_COMPLETED:
                view.run_command('anaconda_complete_funcargs')

            JUST_COMPLETED = False
        elif view.substr(sublime.Region(
                view.sel()[0].begin() - 7, view.sel()[0].end())) == 'import ':
            view.run_command('auto_complete')

    def _complete(self, data):

        proposals = data['completions'] if data['success'] else []

        if proposals:
            active_view().run_command("hide_auto_complete")
            self.completions = proposals
            self.ready_from_defer = True

            active_view().run_command("auto_complete", {
                'disable_auto_insert': True,
                'api_completions_only': get_settings(
                    active_view(), 'hide_snippets_on_completion', False),
                'next_completion_if_showing': False,
                'auto_complete_commit_on_tab': True,
            })


class AnacondaCompleteFuncargs(sublime_plugin.TextCommand):
    """
    Function / Class constructor autocompletion command

    This is directly ported fronm SublimeJEDI
    """

    def run(self, edit, characters=''):
        if not get_settings(self.view, 'complete_parameters', False):
            return

        self._insert_characters(edit)

        location = active_view().rowcol(self.view.sel()[0].begin())
        data = prepare_send_data(location, 'parameters')
        data['settings'] = {
            'complete_parameters': get_settings(
                self.view, 'complete_parameters', False
            ),
            'complete_all_parameters': get_settings(
                self.view, 'complete_all_parameters', False
            )
        }
        Worker().execute(self.insert_snippet, **data)

    @enable_for_python
    def is_enabled(self):
        """Determine if this command is enabled or not
        """

    def _insert_characters(self, edit):
        """
        Insert autocomplete character with closed pair
        and update selection regions

        :param edit: sublime.Edit
        :param characters: str
        """

        regions = [a for a in self.view.sel()]
        self.view.sel().clear()

        for region in reversed(regions):

            if self.view.settings().get('auto_match_enabled', True):
                position = region.end()
            else:
                position = region.begin()

            self.view.sel().add(sublime.Region(position, position))

    def insert_snippet(self, data):
        """Insert the snippet in the buffer
        """

        template = data['template']
        active_view().run_command('insert_snippet', {'contents': template})


class AnacondaGoto(sublime_plugin.TextCommand):
    """Jedi GoTo a Python defunition for Sublime Text
    """

    def run(self, edit):
        try:
            location = active_view().rowcol(self.view.sel()[0].begin())
            data = prepare_send_data(location, 'goto')
            Worker().execute(partial(JediUsages(self).process, False), **data)
        except:
            pass

    @enable_for_python
    def is_enabled(self):
        """Determine if this command is enabled or not
        """


class AnacondaFindUsages(sublime_plugin.TextCommand):
    """Jedi find usages for Sublime Text
    """

    def run(self, edit):
        try:
            location = active_view().rowcol(self.view.sel()[0].begin())
            data = prepare_send_data(location, 'usages')
            Worker().execute(
                partial(JediUsages(self).process, True), **data
            )
        except:
            pass

    @enable_for_python
    def is_enabled(self):
        """Determine if this command is enabled or not
        """


class AnacondaDoc(sublime_plugin.TextCommand):
    """Jedi get documentation string for Sublime Text
    """

    documentation = None

    def run(self, edit):
        if self.documentation is None:
            try:
                location = self.view.rowcol(self.view.sel()[0].begin())
                if self.view.substr(self.view.sel()[0].begin()) in ['(', ')']:
                    location = (location[0], location[1] - 1)

                data = prepare_send_data(location, 'doc')
                Worker().execute(self.prepare_data, **data)
            except Exception as error:
                print(error)
        else:
            self.print_doc(edit)

    @enable_for_python
    def is_enabled(self):
        """Determine if this command is enabled or not
        """

    def prepare_data(self, data):
        """Prepare the returned data
        """

        if data['success']:
            self.documentation = data['doc']
            if self.documentation is None:
                self.view.set_status(
                    'anaconda_doc', 'Anaconda: No documentation found'
                )
                sublime.set_timeout_async(
                    lambda: self.view.erase_status('anaconda_doc'), 5000
                )
            else:
                sublime.active_window().run_command('anaconda_doc')

    def print_doc(self, edit):
        """Print the documentation string into a Sublime Text panel
        """

        doc_panel = self.view.window().create_output_panel(
            'anaconda_documentation'
        )

        doc_panel.set_read_only(False)
        region = sublime.Region(0, doc_panel.size())
        doc_panel.erase(edit, region)
        doc_panel.insert(edit, 0, self.documentation)
        self.documentation = None
        doc_panel.set_read_only(True)
        doc_panel.show(0)
        self.view.window().run_command(
            'show_panel', {'panel': 'output.anaconda_documentation'}
        )


class AnacondaRename(sublime_plugin.TextCommand):
    """Rename the word under the cursor to the given one in its total scope
    """

    data = None

    def run(self, edit):
        if self.data is None:
            try:
                sublime.active_window().show_input_panel(
                    "Replace with:", "", self.input_replacement, None, None
                )
            except:
                logging.error(traceback.format_exc())
        else:
            self.rename(edit)

    @enable_for_python
    def is_enabled(self):
        """Determine if this command is enabled or not
        """

    def input_replacement(self, replacement):
        location = self.view.rowcol(self.view.sel()[0].begin())
        data = prepare_send_data(location, 'refactor_rename')
        data['directories'] = sublime.active_window().folders()
        data['new_word'] = replacement
        Worker().execute(self.store_data, **data)

    def store_data(self, data):
        """Just store the data an call the command again
        """

        self.data = data
        self.view.run_command('anaconda_rename')

    def rename(self, edit):
        """Rename in the buffer
        """

        data = self.data
        if data['success'] is True:
            for filename, data in data['renames'].items():
                for line in data:
                    view = sublime.active_window().open_file(
                        '{}:{}:0'.format(filename, line['lineno']),
                        sublime.ENCODED_POSITION
                    )
                    while view.is_loading():
                        time.sleep(0.01)

                    lines = view.lines(sublime.Region(0, view.size()))
                    view.replace(edit, lines[line['lineno']], line['line'])

        self.data = None


class AnacondaAutoFormat(sublime_plugin.TextCommand):
    """Execute autopep8 formating
    """

    data = None

    def run(self, edit):
        if self.data is not None:
            self.replace(edit)
            return

        aggresive_level = get_settings(self.view, 'aggressive', 0)
        if aggresive_level > 0:
            if not sublime.ok_cancel_dialog(
                'You have an aggressive level of {} this may cause '
                'anaconda to change things that you don\'t really want to '
                'change.\n\nAre you sure do you want to continue?'.format(
                    aggresive_level
                )
            ):
                return

        code = self.view.substr(sublime.Region(0, self.view.size()))
        settings = {
            'aggressive': aggresive_level,
            'list-fixes': get_settings(self.view, 'list-fixes', False),
            'ignore': get_settings(self.view, 'ignore', []),
            'select': get_settings(self.view, 'select', [])
        }
        try:
            messages = {
                'start': 'Autoformatting please wait...',
                'end': 'Autoformatting done!'
            }
            self.pbar = ProgressBar(messages)
            self.pbar.start()
            self.view.set_read_only(True)
            autopep.AnacondaAutopep8(settings, code, self.get_data).start()
        except:
            logging.error(traceback.format_exc())

    def is_enabled(self):
        """Determine if this command is enabled or not
        """

        return is_python(self.view, True)

    def get_data(self, data):
        """Collect the returned data from autopep8
        """

        self.data = data
        self.pbar.terminate()
        self.view.set_read_only(False)
        self.view.run_command('anaconda_auto_format')

    def replace(self, edit):
        """Replace the old code with what autopep8 gave to us
        """

        region = sublime.Region(0, self.view.size())
        self.view.replace(edit, region, self.data)
        self.data = None


def plugin_loaded():
    """Called directly from sublime on plugin load
    """

    package_folder = os.path.dirname(__file__)
    if not os.path.exists(os.path.join(package_folder, 'Main.sublime-menu')):
        template_file = os.path.join(
            package_folder, 'templates', 'Main.sublime-menu.tpl'
        )
        with open(template_file, 'r', encoding='utf8') as tplfile:
            template = Template(tplfile.read())

        menu_file = os.path.join(package_folder, 'Main.sublime-menu')
        with open(menu_file, 'w', encoding='utf8') as menu:
            menu.write(template.safe_substitute({
                'package_folder': os.path.basename(package_folder)
            }))
