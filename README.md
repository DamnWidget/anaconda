# Anaconda

Anaconda turns your Sublime Text 3 into a full featured Python IDE. Read the plugin documentation on [http://damnwidget.github.io/anaconda](http://damnwidget.github.io/anaconda).

[![Build Status](https://www.gitbook.io/button/status/book/damnwidget/anacondast3-developers-documentation)](https://www.gitbook.io/book/damnwidget/anacondast3-developers-documentation/activity)

# Getting Started

Anaconda works out of the box but there are multitude of options and features that you can tune and adapt to your own style or needs.

* [Autocompletion on dot](http://damnwidget.github.io/anaconda/IDE/#toc_3)
* [Powerful IDE](http://damnwidget.github.io/anaconda/IDE/)
* [Advanced Configuration](http://damnwidget.github.io/anaconda/anaconda_settings/)
* [Run Tests using Anaconda](http://damnwidget.github.io/anaconda/tests_runner/)
* [Linting theme customization](http://damnwidget.github.io/anaconda/IDE/#toc_50)
* [Using Vagrant Environments](http://damnwidget.github.io/anaconda/vagrant/)

# License

This program is distributed under the terms of the GNU GPL v3. See the [LICENSE](https://raw.github.com/DamnWidget/anaconda/master/LICENSE) file for details.

# Troubleshootings

Guide to solve common issues

## Anaconda does not appear in the available packages list on Package Control

You have to update your package control version to the version 2.0 or better

## I get errors in the console about "the file can't be open" in worker.py file

Your sublime text can't find the interpreter that you set in your configuration, by default, anaconda set this as `python` so it will get your configured Python interpreter in your PATH (if any)

## Autocomplete for import behaves badly

Sublime Text 3 Python default package decide to cancel the autocompletion when some words are detected (for example `def` or `class`) but it also decides to cancel it with the word `import`.

To fix that behavior and make ST3 use the anaconda's completion create a new Python directory in your Packages directory and copy the contents of the file [Completion Rules.tmPreferences](https://raw.githubusercontent.com/DamnWidget/anaconda/master/Completion%20Rules.tmPreferences) there with the same name.


# Contributing with Anaconda

There are several ways to contribute with anaconda.

**important**: there is a [Developers Documentation book](http://damnwidget.gitbooks.io/anacondast3-developers-documentation/) that is maintained up to date with the last information about anaconda internals and useful information about how to contribute with the project

## Feedback

* By giving feedback about the plugin and how it works in your platform.
* By reporting bugs in the issue tracker
* By sharing your ideas with us

## Bug Hunting

Did you found a bug and you know how to fix it? First of all, thank you very much. You just have to report the bug as a new issue, fork the repository, make your changes and send a new pull request.

## Feature Implementor

So you thougth about a new killer feature to implement in Anaconda?. Great!. Open an issue tagged as "Feature" and we will discuss it with you.

## Donations

Just donate to maintain this project alive.

[![PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=KP7PAHR962UGG&lc=US&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted)
[<img src="https://api.flattr.com/button/flattr-badge-large.png" />][0]
[![githalytics.com alpha](https://cruel-carlota.pagodabox.com/de124b4ffd37f6c0491ee7e4de3ec4cc "githalytics.com")](http://githalytics.com/DamnWidget/anaconda)
[0]: http://flattr.com/thing/1765332/DamnWidgetanaconda-on-GitHub
