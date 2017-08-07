
# Copyright (C) 2015 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import glob
import logging
from string import Template

import sublime

from .helpers import get_settings
from ._typing import Callable, Union, Dict


class Tooltip(object):
    """Just a wrapper around Sublime Text 3 tooltips
    """

    themes = {}  # type: Dict[str, bytes]
    tooltips = {}  # type: Dict[str, str]
    loaded = False
    basesize = 75

    def __init__(self, theme: str) -> None:
        self.theme = theme

        if int(sublime.version()) < 3070:
            return

        if Tooltip.loaded is False:
            self._load_css_themes()
            self._load_tooltips()
            Tooltip.loaded = True

    def show_tooltip(self, view: sublime.View, tooltip: str, content: Dict[str, str], fallback: Callable) -> None:  # noqa
        """Generates and display a tooltip or pass execution to fallback
        """

        st_ver = int(sublime.version())
        if st_ver < 3070:
            return fallback()

        width = get_settings(view, 'font_size', 8) * 75
        kwargs = {'location': -1, 'max_width': width if width < 900 else 900}
        if st_ver >= 3071:
            kwargs['flags'] = sublime.COOPERATE_WITH_AUTO_COMPLETE
        text = self._generate(tooltip, content)
        if text is None:
            return fallback()

        return view.show_popup(text, **kwargs)

    def _generate(self, tooltip: str, content: Dict[str, str]) -> Union[Dict[str, str], None]:  # noqa
        """Generate a tooltip with the given text
        """

        try:
            t = self.theme
            theme = self.themes[t] if t in self.themes else self.themes['popup']  # noqa
            context = {'css': theme}
            context.update(content)
            data = self.tooltips[tooltip].safe_substitute(context)
            return data
        except KeyError as err:
            logging.error(
                'while generating tooltip: tooltip {} don\'t exists'.format(
                    str(err))
            )
            return None

    def _load_tooltips(self) -> None:
        """Load tooltips templates from anaconda tooltips templates
        """

        template_files_pattern = os.path.join(
            os.path.dirname(__file__), os.pardir,
            'templates', 'tooltips', '*.tpl')
        for template_file in glob.glob(template_files_pattern):
            with open(template_file, 'r', encoding='utf8') as tplfile:
                tplname = os.path.basename(template_file).split('.tpl')[0]
                tpldata = '<style>${{css}}</style>{}'.format(tplfile.read())
                self.tooltips[tplname] = Template(tpldata)

    def _load_css_themes(self) -> None:
        """
        Load any css theme found in the anaconda CSS themes directory
        or in the User/Anaconda.themes directory
        """

        css_files_pattern = os.path.join(
            os.path.dirname(__file__), os.pardir, 'css', '*.css')
        for css_file in glob.glob(css_files_pattern):
            logging.info('anaconda: {} css theme loaded'.format(
                self._load_css(css_file))
            )

        packages = sublime.active_window().extract_variables()['packages']
        user_css_path = os.path.join(packages, 'User', 'Anaconda.themes')
        if os.path.exists(user_css_path):
            css_files_pattern = os.path.join(user_css_path, '*.css')
            for css_file in glob.glob(css_files_pattern):
                logging.info(
                    'anaconda: {} user css theme loaded',
                    self._load_css(css_file)
                )

    def _load_css(self, css_file: str) -> str:
        """Load a css file
        """

        theme_name = os.path.basename(css_file).split('.css')[0]
        with open(css_file, 'r') as resource:
            self.themes[theme_name] = resource.read()

        return theme_name
