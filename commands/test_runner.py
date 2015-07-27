
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details


import os
import re
import functools

import sublime
import sublime_plugin
from ..anaconda_lib.helpers import get_settings, git_installation, is_python

DEFAULT_TEST_COMMAND = "nosetests"
TEST_DELIMETER = "."
TB_FILE = r'[ ]*File \"(...*?)\", line ([0-9]*)'


def virtualenv(func):
    """
    Wraps the _prepare_command call to add virtualenv init and stop if the
    `test_virtualenv` is set
    """

    @functools.wraps(func)
    def wrapper(self):
        result = func(self)
        command = result
        virtualenv = get_settings(self.view, 'test_virtualenv')
        if virtualenv is not None:
            cmd = 'source {}/bin/activate'.format(virtualenv)
            if os.name != 'posix':
                cmd = os.path.join(virtualenv, 'Scripts', 'activate')

            command = '{};{};deactivate'.format(cmd, result)

        return command

    return wrapper


class TestMethodMatcher(object):

    """Match a test method under the cursor
    """

    def find_test_path(self, test_file_content, delimeter=TEST_DELIMETER):
        """Try to find the test path, returns None if can't be found
        """

        test_method = self.find_test_method(test_file_content)
        if test_method is not None:
            test_class = self.find_test_class(test_file_content)
            return delimeter + test_class + "." + test_method

    def find_test_method(self, test_file_content):
        """Try to find the test method, returns None if can't be found
        """

        match_methods = re.findall(
            r'\s?def\s+(test_\w+)\s?\(', test_file_content)
        if match_methods:
            return match_methods[-1]  # the last one?

    def find_test_class(self, test_file_content):
        """Try to find the test class, return None if can't be found
        """

        match_classes = re.findall(r'\s?class\s+(\w+)\s?\(', test_file_content)
        if match_classes:
            try:
                return [
                    c for c in match_classes if "Test" in c or "test" in c][-1]
            except IndexError:
                return match_classes[-1]


class AnacondaRunTestsBase(sublime_plugin.TextCommand):

    """
    Run test commands based on project configuration

    For example, for a Django project using nose2:

        "settings": {
            "test_before_command":
                "source ~/.virtualenvs/<PROJECT>/bin/activate",
            "test_command":
                "./manage.py test --settings=tests.settings --noinput",
            "test_after_command": "deactivate",
            // This is the delimiter between the module and the class
            "test_delimeter": ":",  // "." by default
        }
    """

    @property
    def output_syntax(self):
        """
        Property that return back the PythonConsole output syntax.

        This is needed because if anaconda has been installed using git
        the path is different
        """

        return 'Packages/{}/PythonConsole.hidden-tmLanguage'.format(
            'anaconda' if git_installation else 'Anaconda'
        )

    @property
    def output_theme(self):
        """
        Property that return back the PythonConsole output theme.

        This is needed because if anaconda has been installed using git
        the path is different
        """

        theme = get_settings(
            self.view, 'test_runner_theme', 'PythonConsoleDark.hidden-tmTheme')
        return 'Packages/{}/{}'.format(
            'anaconda' if git_installation else 'Anaconda', theme
        )

    @property
    def test_path(self):
        """Return back the tests path
        """

        real_path = os.path.relpath(
            self.view.file_name(), self.test_root).replace(os.sep, '.')
        print(real_path)
        if real_path is not None:
            return real_path[:-3]

        return ""

    def is_enabled(self):
        """Determine if this command is enabled or not
        """

        return is_python(self.view)

    def run(self, edit):
        """Run the test or tests using the configured command
        """

        self._load_settings()
        command = self._prepare_command()
        self._configure_output_window(width=160)
        self.view.window().run_command(
            'exec', {
                'shell_cmd': command,
                'working_dir': self.test_root,
                'syntax': self.output_syntax,
                "file_regex": TB_FILE
            }
        )
        self._save_test_run(command)

    def _load_settings(self):
        sep = ";"
        if os.name == "nt":
            sep = "&"

        gs = get_settings
        self.test_root = gs(
            self.view, 'test_root', self.view.window().folders()[0]
        )
        self.test_command = gs(self.view, 'test_command', DEFAULT_TEST_COMMAND)
        self.before_test = gs(self.view, 'test_before_command')
        if type(self.before_test) is list:
            self.before_test = sep.join(self.before_test)
        self.after_test = gs(self.view, 'test_after_command')
        if type(self.after_test) is list:
            self.after_test = sep.join(self.after_test)
        self.test_delimeter = gs(self.view, 'test_delimeter', TEST_DELIMETER)
        self.output_show_color = gs(self.view, 'test_output_show_color', True)

    @virtualenv
    def _prepare_command(self):
        """Prepare the command to run adding pre tests and after tests
        """

        command = [self.test_command, self.test_path]
        if self.before_test is not None:
            command = [self.before_test, ';'] + command
        if self.after_test is not None:
            command += [';', self.after_test]

        print(command)
        return ' '.join(command)

    def _configure_output_window(self, width=80):
        """Configure the syntax and style of the output window
        """

        panel = self.view.window().get_output_panel('exec')
        panel.settings().set('wrap_width', width,)

        if self.output_show_color:
            panel.settings().set('color_scheme', self.output_theme)

    def _save_test_run(self, command):
        """Save the last ran test
        """

        s = sublime.load_settings('PythonTestRunner.last-run')
        s.set('last_test_run', command)
        sublime.save_settings('PythonTestRunner.last-run')


class AnacondaRunCurrentFileTests(AnacondaRunTestsBase):

    """Run tests in the current file
    """

    @property
    def test_path(self):
        return super(AnacondaRunCurrentFileTests, self).test_path


class AnacondaRunProjectTests(AnacondaRunTestsBase):

    """Run all tests in a project
    """

    @property
    def test_path(self):
        """
        Empty path should run all tests.

        If the option `test_project_path` is set, return it instead
        """
        return get_settings(self.view, 'test_project_path', '')


class AnacondaRunCurrentTest(AnacondaRunTestsBase):

    """Run test under cursor
    """

    @property
    def test_path(self):
        """Return the correct path to run the test under the cursor
        """

        test_path = super(AnacondaRunCurrentTest, self).test_path
        region = self.view.sel()[0]
        line_region = self.view.line(region)
        file_character_start = 0
        text_string = self.view.substr(
            sublime.Region(file_character_start, line_region.end())
        )
        test_name = TestMethodMatcher().find_test_path(
            text_string, delimeter=self.test_delimeter
        )
        if test_name is not None:
            return test_path + test_name

        return ''


class AnacondaRunLastTest(AnacondaRunTestsBase):

    """Run the previous ran test
    """

    def _prepare_command(self):
        s = sublime.load_settings('PythonTestRunner.last-run')
        return s.get('last_test_run')
