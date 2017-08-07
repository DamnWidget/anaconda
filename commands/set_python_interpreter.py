import logging
import traceback

import sublime
import sublime_plugin

from ..anaconda_lib._typing import Dict, Any
from ..anaconda_lib.helpers import is_python
from ..anaconda_lib.builder.python_builder import AnacondaSetPythonBuilder


class AnacondaSetPythonInterpreter(sublime_plugin.TextCommand):
    """Sets or modifies the Venv of the current project"""

    def run(self, edit: sublime.Edit) -> None:
        try:
            sublime.active_window().show_input_panel(
                "Python Path:", self.get_current_interpreter_path(),
                self.update_interpreter_settings, None, None
            )
        except Exception:
            logging.error(traceback.format_exc())

    def update_interpreter_settings(self, venv_path: str) -> None:
        """Updates the project and adds/modifies the Venv path"""
        project_data = self.get_project_data()

        # Check if have settings set in the project settings
        if project_data.get('settings', False):

            try:
                # Try to get the python_interpreter key
                project_data['settings'].get('python_interpreter', False)
            except AttributeError:
                # If this happens that mean your settings is a sting not a dict
                sublime.message_dialog(
                    'Ops your project settings is missed up'
                )
            else:
                # Set the path and save the project
                project_data['settings']['python_interpreter'] = venv_path
                self.save_project_data(project_data)
        else:
            # This will excute if settings key is not in you project settings
            project_data.update(
                {
                    'settings': {'python_interpreter': venv_path}
                }
            )
            self.save_project_data(project_data)
            AnacondaSetPythonBuilder().update_interpreter_build_system(
                venv_path
            )

    def save_project_data(self, data: Dict[str, Any]) -> None:
        """Saves the provided data to the project settings"""
        sublime.active_window().set_project_data(data)
        sublime.status_message("Python path is set successfuly")

    def get_project_data(self) -> Dict[str, Any]:
        """Return the project data for the current window"""
        return sublime.active_window().project_data()

    def get_current_interpreter_path(self) -> str:
        """Returns the current path from the settings if possible"""
        try:
            return self.get_project_data()['settings']['python_interpreter']
        except Exception:
            return ''

    def is_enabled(self) -> bool:
        """Check this plug in is enabled"""
        return is_python(self.view)
