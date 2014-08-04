
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details


import os
import re
import sublime
import sublime_plugin
from ..anaconda_lib.helpers import get_settings

DEFAULT_TEST_COMMAND = "nosetests "
TEST_DELIMETER = ":"


class TestMethodMatcher(object):

    def find_test_path(self, test_file_content, delimeter=TEST_DELIMETER):
        test_method = self.find_test_method(test_file_content)
        if test_method:
            test_class = self.find_test_class(test_file_content)
            return delimeter + test_class + "." + test_method

    def find_test_method(self, test_file_content):
        match_methods = re.findall(r'\s?def\s+(test_\w+)\s?\(', test_file_content)
        if match_methods:
            return match_methods[-1]

    def find_test_class(self, test_file_content):
        match_classes = re.findall(r'\s?class\s+(\w+)\s?\(', test_file_content)
        if match_classes:
            try:
                return [c for c in match_classes if "Test" in c or "test" in c][-1]
            except IndexError:
                return match_classes[-1]


class AnacondaRunTestsBase(sublime_plugin.TextCommand):
    """
    runs test commands based on project config

    example settings for a django project using nose2:

    "settings": {
        "test_before_command": "source ~/.virtualenvs/<PROJECT>/bin/activate",
        "test_command": "./manage.py test --settings=tests.settings --noinput ",
        "test_after_command": "deactivate",
        "test_delimeter": ".",  // this is the delimiter between the module and the class, it is ":" by default
    }

    """

    def run(self, edit):
        self.load_settings()
        self.clean_settings()
        command = self.prepare_command()

        cmd = {
            "cmd": [command],
            "shell": True,
            "working_dir": self.test_root,
        }

        if self.output_show_color:
            cmd["syntax"] = self.output_syntax
        self.configure_output_window(width=160)

        self.view.window().run_command("exec", cmd)
        self.save_test_run(command)

    def load_settings(self):
        self.test_root = get_settings(self.view, 'test_root', self.view.window().folders()[0])
        self.test_command = get_settings(self.view, 'test_command', DEFAULT_TEST_COMMAND)
        self.before_test = get_settings(self.view, 'test_before_command')
        self.after_test = get_settings(self.view, 'test_after_command')
        self.test_delimeter = get_settings(self.view, 'test_delimeter', TEST_DELIMETER)
        self.output_show_color = get_settings(self.view, 'test_output_show_color', True)

        self.output_syntax = "Packages/Anaconda/PythonConsole.hidden-tmLanguage"
        self.output_theme = "Packages/Anaconda/PythonConsoleDark.hidden-tmTheme"

    def clean_settings(self):
        if 'nosetests' in self.test_command:
            if not self.test_command.endswith(' '):
                self.test_command += ' '

    def get_test_path(self):
        """
        returns module path to the current file
        """
        abs_file = self.view.file_name()
        rel_path = os.path.relpath(abs_file, self.test_root)
        self.test_path = rel_path.replace('/', '.')
        return self.test_path[:-3]  # remove .py

    def prepare_command(self):
        command = self.test_command + self.get_test_path()
        if self.before_test:
            command = self.before_test + " ; " + command
        if self.after_test:
            command = command + " ; " + self.after_test
        return command

    def save_test_run(self, command):
        s = sublime.load_settings("PythonTestRunner.last-run")
        s.set("last_test_run", command)
        sublime.save_settings("PythonTestRunner.last-run")

    def configure_output_window(self, width=80):
        panel = self.view.window().get_output_panel('exec')
        panel.set_syntax_file(self.output_syntax)
        panel.settings().set('wrap_width', width,)

        if self.output_show_color:
            panel.settings().set('color_scheme', self.output_theme)


class AnacondaRunCurrentFileTests(AnacondaRunTestsBase):

    """
    run only the tests in the current file
    """

    def get_test_path(self):
        return super(AnacondaRunCurrentFileTests, self).get_test_path()


class AnacondaRunProjectTests(AnacondaRunTestsBase):

    """
    run all tests in the project
    """

    def get_test_path(self):
        """
        empty path should run all tests
        """
        return ""


class AnacondaRunCurrentTest(AnacondaRunTestsBase):

    """
    run only the test the cursor is over
    """

    def get_test_path(self):
        test_path = super(AnacondaRunCurrentTest, self).get_test_path()
        region = self.view.sel()[0]
        line_region = self.view.line(region)
        file_character_start = 0
        text_string = self.view.substr(
            sublime.Region(file_character_start, line_region.end())
        )
        test_name = TestMethodMatcher().find_test_path(
            text_string, delimeter=self.test_delimeter
        )
        if test_name:
            return test_path + test_name


class AnacondaRunLastTest(AnacondaRunTestsBase):

    def prepare_command(self):
        s = sublime.load_settings("PythonTestRunner.last-run")
        return s.get("last_test_run")
