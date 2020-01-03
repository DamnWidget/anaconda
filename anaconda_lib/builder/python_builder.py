
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
from string import Template

import sublime

from ..helpers import get_settings, active_view, is_remote_session


class AnacondaSetPythonBuilder(object):
    """Sets or modifies the builder of the current project
    """

    def update_interpreter_build_system(self, cmd):
        """Updates the project and adds/modifies the build system
        """

        view = active_view()
        if get_settings(view, 'auto_python_builder_enabled', True) is False:
            return

        if is_remote_session(view):
            return

        if cmd is None:
            sublime.message_dialog(
                'Your python interpreter is not set or is invalid'
            )
            return

        project = self._get_project()
        if project.get('build_systems', False) is not False:
            if type(project['build_systems']) is list:
                done = False
                current_list = project['build_systems']
                for i in range(len(current_list)):
                    build = current_list[i]
                    if build['name'] == 'Anaconda Python Builder':
                        current_list[i] = self._parse_tpl(cmd)
                        done = True
                        break

                if not done:
                    project['build_systems'].append(self._parse_tpl(cmd))
            else:
                sublime.message_dialog(
                    'Your project build_systems is messed up'
                )
        else:
            project.update({
                'build_systems': [self._parse_tpl(cmd)]
            })

        self._save_project(project)

    def _get_project(self):
        """Get Project configuration
        """

        return sublime.active_window().project_data()

    def _parse_tpl(self, cmd):
        """Parses the builder template
        """

        template_file = os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'templates', 'python_build.tpl'
        )
        with open(template_file, 'r', encoding='utf8') as tplfile:
            template = Template(tplfile.read())

        cmd = cmd.replace('\\', '\\\\')
        return sublime.decode_value(
            template.safe_substitute({'python_interpreter': cmd})
        )

    def _save_project(self, project_data):
        """Save project configuration
        """

        sublime.active_window().set_project_data(project_data)
