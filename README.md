[![Join the chat at https://gitter.im/DamnWidget/anaconda](https://img.shields.io/gitter/room/DamnWidget/anaconda.svg?maxAge=2592000)](https://gitter.im/DamnWidget/anaconda?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![GitHub release](https://img.shields.io/github/release/damnwidget/anaconda.svg)](https://github.com/DamnWidget/anaconda/releases/latest)
[![Build Status](https://travis-ci.org/DamnWidget/anaconda.svg?branch=master)](https://travis-ci.org/DamnWidget/anaconda)
[![Package Control](https://img.shields.io/packagecontrol/dt/Anaconda.svg)](https://packagecontrol.io/packages/Anaconda)

                                                          |
              _` |  __ \    _` |   __|   _ \   __ \    _` |   _` |
             (   |  |   |  (   |  (     (   |  |   |  (   |  (   |
            \__,_| _|  _| \__,_| \___| \___/  _|  _| \__,_| \__,_|
                                     The Sublime Text 3 Python IDE

[![Pledgie][pledgie-donate-image]][pledgie-donate-link]

Anaconda turns your Sublime Text 3 into a full featured Python IDE. Read the plugin documentation on [http://damnwidget.github.io/anaconda](http://damnwidget.github.io/anaconda).

## Build Status

| Component | Travis CI |
| --- | --- | --- |
| **JsonServer** | [![Build Status](https://travis-ci.org/DamnWidget/anaconda.svg?branch=master)](https://travis-ci.org/DamnWidget/anaconda) |

## Getting Started
Anaconda works out of the box but there are multitude of options and features that you can tune and adapt to your own style or needs.

* [Powerful IDE](http://damnwidget.github.io/anaconda/IDE/)
* [Advanced Configuration](http://damnwidget.github.io/anaconda/anaconda_settings/)
* [Run Tests using Anaconda](http://damnwidget.github.io/anaconda/tests_runner/)
* [Linting theme customization](http://damnwidget.github.io/anaconda/IDE/#toc_50)
* [Using Vagrant Environments](http://damnwidget.github.io/anaconda/vagrant/)

## License
This program is distributed under the terms of the GNU GPL v3. See the [LICENSE][license] file for more details.

## Tooltips
anaconda officially supports user themeable tooltips and displaying advanced signatures. This is how it looks in a dark theme:

![Tooltips Image][tooltips-dark-image]

**Note**: This feature is enabled for users of Sublime Text 3 build 3070 or superior only.

## Troubleshooting
This section lists some common issues faced by users, along with workarounds.

#### Anaconda does not appear in the Available Packages list on Package Control.

**Work-around**: You have to update your Package Control version to the version 2.0 or better.

#### Errors in the console about "the file can't be open" in worker.py file.
Your Sublime Text can't find the interpreter that you set in your configuration, by default, anaconda sets this as `python` so it will get your configured Python interpreter in your PATH (if any).

**Work-around**: Add a Python interpreter (named `python`) to your PATH or set a right full path to your python interpreter as parameter of `python_interpreter` settings option, for example `/usr/local/bin/python3.4`.

#### Auto-complete for import behaves badly.
Sublime Text 3's default Python package cancels the auto-completion when some words are detected (for example `def` or `class`). This list of words includes `import`.

**Work-around**: Create a new Python directory in your Packages directory and copy the contents of the file [Completion Rules.tmPreferences][Completion-Rules] there with the same name.
Delete your Sublime Text Cache file `Cache/Python/Completion Rules.tmPreferences.cache`.

**NOTE**: The cache path can be obtained from the Sublime TExt 3 console using the code `sublime.cache_path()`

#### Auto-complete drop-down shows up incorrectly.
SublimeCodeIntel interferes with anaconda's auto-completion.

**Work-around**: Consider disabling SublimeCodeIntel for Python views or disabling/removing it completely when using anaconda.

#### Anaconda behaves slowly and jsonserver crashes
If you are in POSIX systems (Linux or OS X) take a look at the owner of the anaconda's jsonserver log files, they *must* be owned by your user or the jsonserver would be unable to start up. Log files can be found in:
* GNU/Linux: ~/.local/share/anaconda/logs
* OS X: ~/Library/Logs/anaconda
* Windows: %APPDATA%\\Anaconda\\Logs

## Contributing to Anaconda
There are several ways to contribute with anaconda.

> Note: A [Developers Documentation book][dev-docs] is maintained up to date with the latest information about anaconda's internals and useful information about how to contribute to the project.

### Feedback
Giving feedback about the plugin and how it works in your platform, helps make the plugin better.

### Bug Hunting
Did you found a bug and you know how to fix it? First of all, Thank you very much. You just have to report the bug as a new issue, fork the repository, make your changes and send a new pull request.

### Suggesting and Implementing Features
So you thought of a new killer feature to implement in Anaconda? Great! Open an issue for it and we will discuss it with you.

### Available plugins for Anaconda
Anaconda is a plugable architecture platform itself, it means that anaconda can be extended to offer rich IDE like features to other languages, I created other extensions that brings
anaconda capabilities to other languages, the complete list of them can be shown below

| Language | Web Site | Package Control | Status |
| --- | --- | --- | --- |
| **Go** | https://github.com/DamnWidget/anaconda_go | Yes | Active |
| **Rust** | https://github.com/DamnWidget/anaconda_rust | Yes | Active |
| **PHP** | https://github.com/DamnWidget/anaconda_php | Yes | Active |

Would you like to see your language empowered by anaconda? Use `anaconda_rust` or `anaconda_php` as templates and bring your language to life with anaconda's plugable architecture.


### Donations
Please donate to help keep this project alive.

[![PayPal][paypal-donate-image]][paypal-donate-link]

[license]: https://raw.githubusercontent.com/DamnWidget/anaconda/master/LICENSE
[Completion-Rules]: https://raw.githubusercontent.com/DamnWidget/anaconda/master/Completion%20Rules.tmPreferences
[dev-docs]: http://damnwidget.gitbooks.io/anacondast3-developers-documentation/
[paypal-donate-image]: https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif
[paypal-donate-link]: https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=KP7PAHR962UGG&lc=US&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted
[pledgie-donate-image]: https://pledgie.com/campaigns/32230.png?skin_name=chrome
[pledgie-donate-link]: https://pledgie.com/campaigns/32230
[tooltips-dark-image]: http://damnwidget.github.io/anaconda/img/tooltips.png
