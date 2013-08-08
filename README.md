Anaconda
========

Anaconda is a Python autocompletion and linting plugin for Sublime Text 3. It is inspired in SublimeJEDI and based on SublimeLinter.

A bit of history
----------------

Anaconda was born from my need of use a single plugin to autocomplete and lint python code. There are some other really good plugins for that like SublimeJEDI, SublimePythonIDE or SublimeLinter but them doesn't fully fit my needs so I decided to create my own using the best of them.

[SublimeLinter](https://github.com/SublimeLinter/SublimeLinter) is an awesome plugin for Sublime Text and I strongly recommend its use but it support for Sublime Text 3 is not good enough yet and it's python linting is always based on the version of Python that is running by the Sublime Text 3 plugin server that is Python 3.3 so you get error marks for your totally correct python syntax when you work with Python 2 so it make it pretty useles for Python linting in ST3.

[SublimePythonIDE](https://github.com/JulianEberius/SublimePythonIDE) is really great, is a spin off of [SublimeRope](https://github.com/JulianEberius/SublimeRope) for Sublime Text 2 I helped to write a big part of Sublime Rope and part of SublimePythonIDE but the underlying Rope library is not as good for autocompletions as it is for refactors so it doesn't really fit my needs there.

[SublimeJEDI](https://github.com/srusskih/SublimeJEDI) is pretty nice and it uses the [Jedi](https://github.com/davidhalter/jedi) library to perform autocompletions, Jedi is much better than Rope for autocompletion purposes but I don't like their inter process communication architecture.

Anaconda architecture
---------------------

Anaconda is a client-server architecture application. The plugin start a python standard library ``ThreadingMixIn`` server per Sublime Text 3 open window that receive and send text messages in JSON format.

Because that architecture, **anaconda** can lint or complete with python interpreters different than the built-in Sublime Text 3 python interpreter (3.3). It can complete all the python code that the configured interpreter can see and lint files for that version of the interpreter.

Supported platforms
-------------------

Anaconda has been tested in Linux, Windows and Mac OS X with possitive results. I don't have any option to test the plugin in Mac OS X so I depend completely on the community for this task. Several users tested the plugin in Mac OS X with really possitive feedback.

There are some performance problems on Windows that have to ve fixed. You can follow the discussion about that in https://github.com/DamnWidget/anaconda/issues/10

The status of the plugin in the different platforms is:

* **Linux**: Stable
* **Mac OS X**: Stable
* **Windows**: Performance Problems (almost unusable)

Installation
------------

#### Using Package Control

1. Open Sublime Text Command Pallete and type "install" with no quotes
2. Select "Install Package" from the dropdown box
3. Type "anaconda" with no quotes, select it and press `<ENTER>`

#### Using git

Go to your sublime text 3 packages directory and clone the repo:

    git clone https://github.com/DamnWidget/anaconda.git Anaconda

Anaconda autocompletion
-----------------------

Goto and Find Usages implementations are strongly inspired in SublimeJEDI ones, SublimeJEDI is [GNU LGPL v3](http://www.gnu.org/licenses/lgpl.txt) licensed, you can read it online.

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

You can add additional python extra paths that should be used for autocompletion purposes setting a list of paths separated by comma using the user setting ``extra_paths``:

    {
        // ...

        "settings": {
            "extra_paths": "/opt/sublime_text_3,/usr/share/mypythonpackage"
        }
    }

#### Autocompletion on dot

If you want to trigger autocompletion when you write down the dot character you can setup this desirable behaviour editing your Sublime Text 3 ``Python.sublime-settings`` file in ``Packages/User`` (you may have to create this file yourself):

    {
        // ...
        "auto_complete_triggers": [{"selector": "source.python - string - comment - constant.numeric", "characters": "."}]
    }

#### Word and Explicit Sublime Text 3 Completions

Some developers preffer that SublimeText 3 does not autocomplete by itself so you can disable word and explicit autocompletiond setting ``suppress_word_completions`` and ``suppress_explicit_completions`` as ``true``.

Anaconda IDE Features
---------------------

#### Goto Definition

With this command you can go to a file where a variable, function or class that your cursor is over is defined.

* Shortcut: Linux and Windows `super+g`, Mac OS X `ctrl+alt+g`
* Context Menu: `Anaconda > Goto Definition`

#### Find Usages

With this command you can find all the places where a variable, function or class where your cursor is over is being used.

* Shortcut: Linux and Windows `super+f`, Mac OS X `ctrl+alt+f`
* Context Menu: `Anaconda > Find Usages`

#### Get Documentation

With this command you can get the docstring of whatever function or method. You can just write the function call, for example, sys.exit() and then use this command to get the function signature and docstring without lose the cursor focus from the buffer.

* Shortcut: Linux and Windows `super+d`, Mac OS X `ctrl+alt+d`
* Context Menu: `Anaconda > Show Documentation`

*note*: Context menu only works on Python code (no comments, no docstrings)

Anaconda linting
----------------

Anaconda linting is mainly based/inspired/ported from SublimeLinter because that I add the SublimeLinter LICENSE file in the repo.

#### Disabling the linter

Just set the user setting ``anaconda_linting`` as ``false``

#### Linting behaviour

* **Always mode (default)** - When ``anaconda_linting_behaviour`` is set as ``always`` the linting is performed in the background as you are editing the file you are working on and in load/save events. The linting process is performed in the background in another thread of execution and it doesn't block the Sublime Text GUI. The process is fired when the plugin detected that you stop typying for a period of time, by default is half a second and can be configured editign the value of the user setting ``anaconda_linter_delay``.
* **Load and Save mode** - When ``anaconda_linting_behaviour`` is set as ``load-save`` linting is performed on file load and saving only.
* **Save only mode** - When ``anaconda_linting_behabiour`` is set as ``save-only`` linting is performed on file saving only.


#### Disabling pep8

If you don't care about pep8 linting (you are terribly wrong) you can disable pep8 linting at all setting the user setting ``pep8`` as ``false``


#### Disabling certain errors

If what you want to do is just disable some errors like `"line too long"` `E501` error in pep8 (you are terribly wrong again) you can add it to the ``pep8_ignore`` user setting like:

    "pep8_ignore":
    [
        "E501"
    ]

There is an equivalen for PyFlakes errors called ``pyflakes_ignore``, look at the default anaconda configuration file for more details.


#### Gutter Marks

If you want to see gutter marks in the linted lines you just have to set as ``true`` the ``anaconda_gutter_marks`` user setting. Anaconda does't support fancy PNG gutter marks, I never use them so I don't care about, if someone miss them just open an improvement ticket.


#### Linting theme customization

To customize the linting marks like you did in SublimeLinter add the following to your Sublime Text theme (you can ofcourse change the colors to your needs):

    <!-- Anaconda -->
    <dict>
      <key>name</key>
      <string>anaconda Error Outline</string>
      <key>scope</key>
      <string>anaconda.outline.illegal</string>
      <key>settings</key>
      <dict>
          <key>background</key>
          <string>#FF4A52</string>
          <key>foreground</key>
          <string>#FFFFFF</string>
      </dict>
    </dict>
    <dict>
      <key>name</key>
      <string>anaconda Error Underline</string>
      <key>scope</key>
      <string>anaconda.underline.illegal</string>
      <key>settings</key>
      <dict>
          <key>background</key>
          <string>#FF0000</string>
      </dict>
    </dict>
    <dict>
      <key>name</key>
      <string>anaconda Warning Outline</string>
      <key>scope</key>
      <string>anaconda.outline.warning</string>
      <key>settings</key>
      <dict>
          <key>background</key>
          <string>#DF9400</string>
          <key>foreground</key>
          <string>#FFFFFF</string>
      </dict>
    </dict>
    <dict>
      <key>name</key>
      <string>anaconda Warning Underline</string>
      <key>scope</key>
      <string>anaconda.underline.warning</string>
      <key>settings</key>
      <dict>
          <key>background</key>
          <string>#FF0000</string>
      </dict>
    </dict>
    <dict>
      <key>name</key>
      <string>anaconda Violation Outline</string>
      <key>scope</key>
      <string>anaconda.outline.violation</string>
      <key>settings</key>
      <dict>
          <key>background</key>
          <string>#ffffff33</string>
          <key>foreground</key>
          <string>#FFFFFF</string>
      </dict>
    </dict>
    <dict>
      <key>name</key>
      <string>anaconda Violation Underline</string>
      <key>scope</key>
      <string>anaconda.underline.violation</string>
      <key>settings</key>
      <dict>
          <key>background</key>
          <string>#FF0000</string>
      </dict>
    </dict>

#### License

This program is distributed under the terms of the GNU GPL v3. See the [LICENSE](https://raw.github.com/DamnWidget/anaconda/master/LICENSE) file for details.

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

#### Mac OS X machine donator

Do you have a Mac OS X box that you don't use anymore and its abandoned in a corner? Just send it to us, put yourself in contact with us and lets talk.

*note*: we need only one so this section will disappear in the future

### Donations

Just donate to maintain this project alive.

[<img src="https://api.flattr.com/button/flattr-badge-large.png" />][0]

[0]: http://flattr.com/thing/1765332/DamnWidgetanaconda-on-GitHub