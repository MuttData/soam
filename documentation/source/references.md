# Libraries by relevance
This is the priority order to understand the dependencies:

 1. prefect
 2. alembic
 3. sqlalchemy
 4. jinja?
 5. cookiecuter
 6. darts

[//comment]: # (TODO: Ask Pedro to improve the background documents
 with the knowledge learned from delver)

# Slack
In our slack there is a channel #dev-soam, were we discuss project design
details, libraries and issues. There are also some other project related
documents pinned for you to read on.


# Theorical background references

## Backtesting
### Window policies
To do backtesting the data is splited in train and validation, there are two spliting
methods:
 - sliding: create a fixed size window for the training data that ends at the beginning
 of the validation data.
 - expanding: create the training data from remaining data since the start of the series
 until the validation data.

For more information review this document: https://eng.uber.com/backtesting-at-scale/

# Core libraries references
This section contains references to the different libraries and their
associated project files.

## numpydoc
All the documents use numpydoc to document.

https://numpydoc.readthedocs.io/en/latest/format.html

## sphinx
The numpydoc documentation is collected by sphinx.

https://www.sphinx-doc.org/en/master/

## logging
The whole project uses the logging module from the standard library.

https://docs.python.org/3/library/logging.html

## typing
The whole project uses type hinting.

https://docs.python.org/3/library/typing.html


## muttlib
Used in: cfg.py, helpers.py, savers.py

https://gitlab.com/mutt_data/muttlib

## pathlib
Used in: cfg.py, forecast_plotter.py, helpers.py, mail_report.py, savers.py,
slack_report.py, utils.py

https://docs.python.org/3/library/pathlib.html
https://docs.python.org/3/library/pathlib.html#operators


## pkg_resources
Used in: cfg.py, console.py

https://setuptools.readthedocs.io/en/latest/pkg_resources.html


## decouple
Used in: cfg.py

https://github.com/henriquebastos/python-decouple/

## click
Used in: console.py

https://click.palletsprojects.com/en/7.x/


## cookiecutter
Used in: console.py

https://cookiecutter.readthedocs.io/en/latest/


## datetime
Used in: constants.py, helpers.py, plot_utils.py, runner.py

https://docs.python.org/3/library/datetime.html


## sqlalchemy
Used in: data_models.py, helpers.py

https://docs.sqlalchemy.org/en/13/


## pandas
Used in: forecast_plotter.py, helpers.py, plot_utils.py, savers.py,
slack_report.py, step.py, utils.py

https://pandas.pydata.org/pandas-docs/stable/


## contextlib
Used in: helpers.py

https://docs.python.org/3/library/contextlib.html


## Abstract Base Classes
Used in: helpers.py, savers.py, step.py

https://docs.python.org/3/library/abc.html

## scikit-learn
Used in: helpers.py, step.py

https://scikit-learn.org/stable/glossary.html

## smtplib
Used in: mail_report.py

https://docs.python.org/3/library/smtplib.html

## email std lib
Used in: mail_report.py

https://docs.python.org/3/library/email.html


## matplotlib
Used in: plot_utils.py

https://matplotlib.org/3.3.1/contents.html

## numpy
Used in: plot_utils.py

https://numpy.org/doc/

## prefect
Used in: runner.py, savers.py, step.py

https://docs.prefect.io/core/development/documentation.html

## filelock
Used in: savers.py

https://github.com/benediktschmitt/py-filelock

## slackapi
Used in: slack_report.py


https://github.com/slackapi/python-slackclient

## copy
Used in: utils.py

https://docs.python.org/3/library/copy.html

# CI libraries references

https://nox.thea.codes/en/stable/
http://mypy-lang.org/
https://github.com/PyCQA/pylint
https://pycqa.github.io/isort/
https://github.com/psf/black
https://bandit.readthedocs.io/en/latest/
https://pythonhosted.org/theape/documentation/developer/explorations/explore_graphs/explore_pyreverse.html