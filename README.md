Anaconda
========

Anaconda is a python development suite that includes autocompletion, IDE features, linting with PyLint or PyFlakes + pep8, AutoPEP8 , Vagrant and more for Sublime Text 3.

With performance in mind
------------------------

Are you tired of extensions that promise you nice features but make your Sublime Text freezes and blocks while you are typing?. Well, we too, this is why the main goal of anaconda is the performance. Anaconda will never freeze your Sublime Text as everything in anaconda runs asynchronous.

It doesn't matters if you are linting a file with a few hundred or a few thousands of lines, anaconda will work smooth in each situation making you
focus in your code and not interrupting your typing each few seconds.

A bit of history
----------------

Anaconda was born from my need of use a single plugin to autocomplete and lint python code. There are some other really good plugins for that but them doesn't fully fit my needs so I decided to create my own using the best of them.

Anaconda architecture
---------------------

Anaconda is an `asynchronous client-server` architecture application. It starts a new server instance for any open Sublime Text window that contains Python code.

Because that architecture, **anaconda** can lint or complete with python interpreters different than the built-in Sublime Text 3 python interpreter (3.3). It can complete all the python code that the configured interpreter can see and lint files for that version of the interpreter.

Supported platforms
-------------------

Anaconda has been tested in Linux, Windows and Mac OS X with excelent results. The status of the plugin in the different platforms is:

* **Linux**: Stable
* **OS X**: Stable
* **Windows**: Stable

You can run the plugin in profiling mode on Windows (Sublime Text doesn't support cProfile in POSIX platforms) setting the user variable `anaconda_debug` to `profiler`, then you will get a profiling support of where the plugin is spending the processor time.

Those profiles are really helpful for us to fix bugs and solve performance problems on Windows, add it to your issues reports always that you can.

Anaconda Plugins
----------------

Anaconda now support a pluggable interface so other language lintin/completion is possible using the non blocking architecture built into anaconda.

A list of available anaconda plugins below:

* [AnacondaPHP](https://github.com/DamnWidget/anaconda_php) PHP linter, code standard checker and mess detector

Project and Python Interpreter Switching
----------------------------------------

If you change your configured python intrepreter or you just switch your project, anaconda will detect it and reload a new completion/linting/IDE server killing the old one in a total transparent way so you don't need to restart your Sublime Text 3.

Installation
------------

#### Using Package Control

1. Open Sublime Text Command Pallete and type "install" with no quotes
2. Select "Install Package" from the dropdown box
3. Type "anaconda" with no quotes, select it and press `<ENTER>`

#### Using git

Go to your sublime text 3 packages directory and clone the repo:

    git clone https://github.com/DamnWidget/anaconda.git Anaconda

Where to place Anaconda settings options?
-----------------------------------------

You can place anaconda settings in three different places.

    1. Anaconda.sublime-settings global settings file
    2. Anaconda.sublime-settings user settigs file
    3. Project files

If you use the first and second options, take into account that you are configuring anaconda globally for any Python file in any project. To use those two files just go to `Preferences -> Package Settings->Anaconda` then there is a `Settings-Default` and `Settings-User` for options 1 and 2 respectively. Any option in those files have to be places in the global scope.

```json
{
    "python_interpreter": "stackless_python3",
    "auto_python_builder_enabled": false,
    ...
}
```

If you want to override any anaconda settings in specific projects (the `python_interpreter` for example) you can add all the configuration options that you need into your specific Sublime Text project file. In that case, the options must be placed inside the `settings` dictionary of the project configuration file.

```json
{
    "build_systems":
	[
		{
			"name": "Anaconda Python Builder",
			"selector": "source.python",
			"shell_cmd": "/home/damnwidget/.virtualenvs/txorm/bin/python -u \"$file\""
		}
	],
	"folders":
	[
		{
			"follow_symlinks": true,
			"path": "."
		}
	],
	"settings":
	{
		"python_interpreter": "/home/damnwidget/.virtualenvs/txorm/bin/python",
		"auto_python_builder_enabled": false,
		...
	}
}
```


Anaconda autocompletion
-----------------------

Anaconda autocompletion work out of the box but it can be configured with several options.

#### Python interpreter settings

**Anaconda** will use your ``PATH`` configured python interpreter by default. You can change it just editing the ``python_interpreter`` user setting in the **anaconda**'s default configuration file:

    "python_interpreter": "/usr/bin/pypy-c2.0"

You can of course configure the python interpreter to use in a `per-project` basis. To do that, you have to edit your ``<project_name>.sublime-project`` file and override the ``python_interpreter`` user setting there:

    {
        // ...

        "settings": {
            "python_interpreter": "/home/damnwidget/.virtualenvs/mamba-pypy/bin/python"
        }
    }

**Note**: refer to [Howto Configure Anaconda Section](https://github.com/DamnWidget/anaconda/blob/master/README.md#) for more information about anaconda configuration.

You can add additional python extra paths that should be used for autocompletion purposes setting a list of paths using the user setting ``extra_paths``:

    {
        // ...

        "settings": {
            "extra_paths":
            [
                "/opt/sublime_text_3",
                "/usr/share/mypythonpackage"
            ]
        }
    }

Virtualenv environment variables
--------------------------------

If you are using a virtualenv for your `python_interpreter` and you start your Sublime Text 3 from the command line (to inherit environment variables) you can use the variable `$VIRTUAL_ENV` in your `python_interpreter` setting, for example:

    {
        // ...

        "settings": {
            "python_interpreter": "$VIRTUAL_ENV/bin/python"
        }
    }

**note**: if you use the `$VIRTUAL_ENV` variable in your `python_interpreter` but it is missing in the `os.environ` anaconda will fallback to `python`.


#### Environment hook files

If a valid environment hook config file (called ```.anaconda```) exists in the root of your working folder
or in any directory level up to drive root folder, it will be used instead of project or general anaconda
configuration. A valid ```.anaconda```  hook file is as follows.

    {
        "python_interpreter": "pypy-c2.0",
        "extra_paths": ["/usr/local/lib/awesome_lib"]
    }

Note that only ```python_interpreter``` and ```extra_paths``` can be hooked.


#### Autocompletion on dot

If you want to trigger autocompletion when you write down the dot character you can setup this desirable behaviour editing your Sublime Text 3 ``Python.sublime-settings`` file in ``Packages/User`` (you may have to create this file yourself):

    {
        // ...
        "auto_complete_triggers": [{"selector": "source.python - string - comment - constant.numeric", "characters": "."}]
    }

#### Word and Explicit Sublime Text 3 Completions

Some developers preffer that SublimeText 3 does not autocomplete by itself so you can disable word and explicit autocompletion setting ``suppress_word_completions`` and ``suppress_explicit_completions`` as ``true``.

#### Python snippets

You can choose to don't show Python snippets in your autocompletion results placing a user setting `hide_snippets_on_completion` as true in your settings.

#### Complete function and class parameters

If `complete_parameters` is `true`, anaconda will add function and class parameters to its completions when you type `(` after a completion.

If `complete_all_parameters` is `true`, it will add all the possible parameters, if it's false, it will add only required parameters

No key binding is needed to use this feature so it doesn't interfere in any way with your Sublime Text 3 normal operations.

Anaconda IDE Features
---------------------

#### Goto Definition

With this command you can go to a file where a variable, function or class that your cursor is over is defined.

* Shortcut: Linux `super+g`, Mac OS X and Windows `ctrl+alt+g`
* Vintage Mode Shortcut (Command Mode): `gd`
* Context Menu: `Anaconda > Goto Definition`

#### Find Usages

With this command you can find all the places where a variable, function or class where your cursor is over is being used.

* Shortcut: Linux `super+f`, Mac OS X and Windows `ctrl+alt+f`
* Context Menu: `Anaconda > Find Usages`

#### Get Documentation

With this command you can get the docstring of whatever function or method. You can just write the function call, for example, sys.exit() and then use this command to get the function signature and docstring without lose the cursor focus from the buffer.

* Shortcut: Linux `super+d`, Mac OS X and Windows `ctrl+alt+d`
* Context Menu: `Anaconda > Show Documentation`

*note*: Context menu only works on Python code (no comments, no docstrings)
*note*: If you set the option ```"display_signatures"``` as ```true```, anaconda will display method signatures and other help strings in the status bar while you edit the file.

#### Refactor Rename

With this command you can rename the object under the cursor in a project basis scope in a safe way.

* Context Menu: `Anaconda > Rename object under cursor`

#### McCabe code complexity checker

You can run the [McCabe complexity checker](http://en.wikipedia.org/wiki/Cyclomatic_complexity) tool in whatever python file you want. You can configure it threshold adjusting the option setting ```mccabe_threshold``` in the configuration file or in your project configuration file.

* Context Menu: `Anaconda > McCabe complexity check`

#### Autoformat PEP8 Errors

Anaconda supports the [AutoPEP8](https://github.com/hhatto/autopep8) tool and its integrated as part of the plugin itself. You can reformat your files to follow PEP8 automatically using the command palette `Anaconda: Autoformat PEP8 Errors` or the same option in the contextual menu. Of course this operation is performed asynchronous but it set your current buffer as read only while the operation is performed, a progress bar is shown at the status bar while working.

Anaconda can fix the following [PEP8 errors](https://github.com/DamnWidget/anaconda/wiki/PEP8-autoformat-error-list)

Please, take a look at the configuration file to get a list of available options.

* Shortcut: Linux `super+r`, Mac OS X and Windows `ctrl+alt+r`
* Context Menu: `Anaconda > Autoformat PEP8 Errors`

#### Autoimport undefined names

Anaconda will add an `import <undefined_name>` at the end of your imports block if you use the context menu Autoimport anaconda option using the right mouse click over an undefined name in your buffer. Note that anaconda will NOT check if that is a valid import or not.

#### Validating Imports

Anaconda can validate the imports in your files if the configuration option `validate_imports`
is set to `true`.

This feature is disabled by default.

**Note**: Some times, the imports validation mechanism doesn't work too well
with relative imports, because that, you can add `# noqa` at the end of an
import that is mark as invalid if you are sure that anaconda is not handling
well relative paths

Anaconda linting
----------------

Anaconda linting is mainly based/inspired/ported from SublimeLinter because that I added the SublimeLinter LICENSE file in the repo. Although anaconda linter is inspired in SublimeLinter, anaconda linting is much faster for serveral reasons:

1. Anaconda does not use a delayed queue to perform the lintin work, instead of that we fire a single call to the linter methods `n` seconds after the last key was pressend by the user while typing. Those `n` seconds can be configured by the user.
2. Anaconda is totally asynchronous so we should never block the gui, because that, our linting is smooth and flawless.

#### Disabling the linter

Just set the user setting ``anaconda_linting`` as ``false``

#### Disabling the linter in certain files

Sometimes we have to open some file from this mate that all of us have that doesn't seems to know what PEP-8 means and when the teacher spoke about code conventions and readability of the code he was just sick in home and we are just annoyed by the linter marking everyone line of the code.

On this situations we can just disable the linting for this specific file using the command `Anaconda: Disable linting on this file` from the command palette.

When our mate learns how to write proper and clean code we can just turn it on again with `Anaconda: Enable linting on this file`.

#### Disabling specific PyFlakes errors

You can disable specific PyFlakes errors (unused import module for example) uncommenting it in the ``pyflakes_explicit_ignore`` list in the configuration file or adding this list to your project configuration and adding there the type of warnings/errors that you want to disable.

#### Showing linting error list

You can show a quick panel with all the errors in the file you are currently editing usign the command palette or the contextual menu.

#### Jump to the next error

You can use the `Anaconda: Next lint error` command from the `Command Palette`, from the `Context Menu` or just add a shortcut to the `anaconda_next_lint_error` to navigate trough the lint errors on the file.

Note: The order is not per line but for error severity in this order: ERRORS, WARNINGS, VIOLATIONS

#### Linting behaviour

* **Always mode (default)** - When ``anaconda_linting_behaviour`` is set as ``always`` the linting is performed in the background as you are editing the file you are working on and in load/save events. The linting process is performed in the background in another thread of execution and it doesn't block the Sublime Text GUI. The process is fired when the plugin detected that you stop typying for a period of time, by default is half a second and can be configured editign the value of the user setting ``anaconda_linter_delay``.
* **Load and Save mode** - When ``anaconda_linting_behaviour`` is set as ``load-save`` linting is performed on file load and saving only.
* **Save only mode** - When ``anaconda_linting_behabiour`` is set as ``save-only`` linting is performed on file saving only.

#### Enabling pep257

Anaconda supports docsrings linting using [pep257](http://legacy.python.org/dev/peps/pep-0257/) specification. This feature is disabled by default but can be enabled setting `pep257` as `true` in the configuration file.

#### Disabling certain errors for pep257

Specific errors can be disabled adding them (as string elements into a list) on the `pep257_ignore` user settings in the config file. The `D209` is disabled by default as it has been deprecated.


#### Disabling pep8

If you don't care about pep8 linting (you are terribly wrong) you can disable pep8 linting at all setting the user setting ``pep8`` as ``false``


#### Disabling certain errors

If what you want to do is just disable some errors like `"line too long"` `E501` error in pep8 (you are terribly wrong again) you can add it to the ``pep8_ignore`` user setting like:

    "pep8_ignore":
    [
        "E501"
    ]

There is an equivalen for PyFlakes errors called ``pyflakes_ignore``, look at the default anaconda configuration file for more details.

#### Using PyLint as PyFlakes and pep8 alternatives

Anaconda has full support for PyLint as linter application but some considerations has to be taken before do it.

Due 3rd party dependencies required for PyLint, Anaconda does not add it like do with pep8 and PyFlakes libraries, if you want to use PyLint as your linter you have to donwload and install it yourself.

Anaconda does not use a subprocess to call the PyLint linter like Pylinter plugin does. We just import some files from pylint and run the linter from the jsonserver process capturing the system stdout file descriptor. That means anaconda *will* use your configured python interpreter (and environment) in order to lint your files with PyLint so it should be installed in your virtualenvironment if you are using virtualenv.

PyLint *does not* support lint buffers that are not saved yet in the file system so it *can't* lint files before you save it.

Anaconda uses E, W and V codes to maintain compatibility with PyFlakes and PEP8 linters so the PyLint mapping is as follows:

    mapping = {
      'C': 'V',
      'E': 'E',
      'F': 'E',
      'I': 'V',
      'R': 'W',
      'W': 'W'
    }

PyLint errors can be ignored using the setting parameter `pylint_ignore`.

When you use PyLint, PyFlakes and PEP8 are totally turned off.

*Note*: PyLint can be really annoying use it at your own risk

#### Gutter Marks


If you want to see gutter marks in the linted lines you just have to set as ``true`` the ``anaconda_gutter_marks`` user setting. This will add simple marks to gutter. If you want to add fancy icons you can set ``anaconda_gutter_theme`` user settings. Available options are:

- basic (default)
- alpha
- bright
- dark
- hard
- simple

#### Error lines mark

You can control the way that anaconda mark the error lines in your files adjusting the setting `anaconda_linter_mark_style`

* If it's set to `outline` (default) anaconda will outline error lines
* If it's set to `fill` anconda will fill the lines
* If it's set to `none` anaconda will not draw anything on error lines

#### Error underlines

If you don't want to show the red underline under the errors on the lines, you can set the `anaconda_linter_underlines` as false. Note that this option only takes effect when the `anaconda_linter_mark_style` is set to `none`.

#### [Run Tests using Anaconda](https://github.com/DamnWidget/anaconda/wiki/Using-test-runner)

#### [Linting theme customization](https://github.com/DamnWidget/anaconda/wiki/Linting-theme-customization)

#### Vagrant integration

* [Vagrant commands integration](https://github.com/DamnWidget/anaconda/wiki/Using-Vagrant-commands)
* [Using Vagrant Environments](https://github.com/DamnWidget/anaconda/wiki/Vagrant-Environments)

#### License

This program is distributed under the terms of the GNU GPL v3. See the [LICENSE](https://raw.github.com/DamnWidget/anaconda/master/LICENSE) file for details.

Troubleshootings
----------------

Guide to solve common issues

#### Anaconda does not appear in the available packages list on Package Control

You have to update your package control version to the version 2.0 or better

#### I get errors in the console about "the file can't be open" in worker.py file

Your sublime text can't find the interpreter that you set in your configuration, by default, anaconda set this as `python` so it will get your configured Python interpreter in your PATH (if any)

Contributing with Anaconda
--------------------------

There are several ways to contribute with anaconda.

#### Feedback

* By giving feedback about the plugin and how it works in your platform.
* By reporting bugs in the issue tracker
* By sharing your ideas with us

#### Bug Hunting

Did you found a bug and you know how to fix it? First of all, thank you very much. You just have to report the bug as a new issue, fork the repository, make your changes and send a new pull request.

#### Feature Implementor

So you thougth about a new killer feature to implement in Anaconda?. Great!. Open an issue tagged as "Feature" and we will discuss it with you.

### Donations

Just donate to maintain this project alive.

[![PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=KP7PAHR962UGG&lc=US&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted)
[<img src="https://api.flattr.com/button/flattr-badge-large.png" />][0]
[![githalytics.com alpha](https://cruel-carlota.pagodabox.com/de124b4ffd37f6c0491ee7e4de3ec4cc "githalytics.com")](http://githalytics.com/DamnWidget/anaconda)
[0]: http://flattr.com/thing/1765332/DamnWidgetanaconda-on-GitHub
