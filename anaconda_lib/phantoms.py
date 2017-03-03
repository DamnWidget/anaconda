
# Copyright (C) 2015 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import glob
import logging
from string import Template

import sublime

from .helpers import get_settings


class Phantom(object):
    """Just a wrapper around Sublime Text 3 phantoms
    """

    themes = {}  # type: Dict[str, bytes]
    templates = {}  # type: Dict[str, str]
    loaded = False
    phantomsets = {}

    def __init__(self) -> None:
        if int(sublime.version()) < 3124:
            return

        if Phantom.loaded is False:
            self._load_css_themes()
            self._load_phantom_templates()
            Phantom.loaded = True

    def clear_phantoms(self, view):
        if not self.loaded:
            return

        vid = view.id()
        if vid in self.phantomsets:
            self.phantomsets[vid].update([])

    def update_phantoms(self, view, phantoms):
        if not self.loaded:
            return

        thmname = get_settings(view, 'anaconda_linter_phantoms_theme', 'phantom')
        tplname = get_settings(view, 'anaconda_linter_phantoms_template', 'default')

        thm = self.themes.get(thmname, self.themes['phantom'])
        tpl = self.templates.get(tplname, self.templates['default'])

        vid = view.id()
        if vid not in self.phantomsets:
            self.phantomsets[vid] = sublime.PhantomSet(view, 'Anaconda')

        sublime_phantoms = []
        for item in phantoms:
            region = view.full_line(view.text_point(item['line'], 0))
            context = {'css': thm}
            context.update(item)
            content = tpl.safe_substitute(context)
            sublime_phantoms.append(sublime.Phantom(region, content, sublime.LAYOUT_BLOCK))

        self.phantomsets[vid].update(sublime_phantoms)

    def _load_phantom_templates(self) -> None:
        """Load phantoms templates from anaconda phantoms templates
        """

        template_files_pattern = os.path.join(
            os.path.dirname(__file__), os.pardir,
            'templates', 'phantoms', '*.tpl')
        for template_file in glob.glob(template_files_pattern):
            with open(template_file, 'r', encoding='utf8') as tplfile:
                tplname = os.path.basename(template_file).split('.tpl')[0]
                tpldata = '<style>${{css}}</style>{}'.format(tplfile.read())
                self.templates[tplname] = Template(tpldata)

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
