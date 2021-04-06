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

For more information review this document: [backtesting at scale](https://eng.uber.com/backtesting-at-scale/)

# Core libraries references
This section contains references to the different libraries and their
associated project files.

## numpydoc
All the documents use numpydoc to document.

[numpydoc docs](https://numpydoc.readthedocs.io/en/latest/format.html)

## sphinx
The numpydoc documentation is collected by sphinx.

[sphinx docs](https://www.sphinx-doc.org/en/master/)

## logging
The whole project uses the logging module from the standard library.

[logging docs](https://docs.python.org/3/library/logging.html)

## typing
The whole project uses type hinting.

[typing docs](https://docs.python.org/3/library/typing.html)


## muttlib
Used in: cfg.py, helpers.py, savers.py

[muttlib gitlab](https://gitlab.com/mutt_data/muttlib)

## pathlib
Used in: cfg.py, forecast_plotter.py, helpers.py, mail_report.py, savers.py,
slack_report.py, utils.py

[pathlib docs](https://docs.python.org/3/library/pathlib.html) <br>
[pathlib operators](https://docs.python.org/3/library/pathlib.html#operators)


## pkg_resources
Used in: cfg.py, console.py

[pkg_resources docs](https://setuptools.readthedocs.io/en/latest/pkg_resources.html)


## decouple
Used in: cfg.py

[decouple github](https://github.com/henriquebastos/python-decouple/)

## click
Used in: console.py

[click docs](https://click.palletsprojects.com/en/7.x/)


## cookiecutter
Used in: console.py

[cookiecutter docs](https://cookiecutter.readthedocs.io/en/latest/)


## datetime
Used in: constants.py, helpers.py, plot_utils.py, runner.py

[datetime docs](https://docs.python.org/3/library/datetime.html)


## sqlalchemy
Used in: data_models.py, helpers.py

[sqlalchemy docs](https://docs.sqlalchemy.org/en/13/)


## pandas
Used in: forecast_plotter.py, helpers.py, plot_utils.py, savers.py,
slack_report.py, step.py, utils.py

[pandas docs](https://pandas.pydata.org/pandas-docs/stable/)


## contextlib
Used in: helpers.py

[contextlib docs](https://docs.python.org/3/library/contextlib.html)


## Abstract Base Classes
Used in: helpers.py, savers.py, step.py

[abc docs](https://docs.python.org/3/library/abc.html)

## scikit-learn
Used in: helpers.py, step.py

[scikit-learn glossary](https://scikit-learn.org/stable/glossary.html)

## smtplib
Used in: mail_report.py

[smtplib docs](https://docs.python.org/3/library/smtplib.html)

## email std lib
Used in: mail_report.py

[email std lib docs](https://docs.python.org/3/library/email.html)


## matplotlib
Used in: plot_utils.py

[matplotlib contents](https://matplotlib.org/3.3.1/contents.html)

## numpy
Used in: plot_utils.py

[numpy docs](https://numpy.org/doc/)

## prefect
Used in: runner.py, savers.py, step.py

[prefect docs](https://docs.prefect.io/core/development/documentation.html)

## filelock
Used in: savers.py

[fileloc github](https://github.com/benediktschmitt/py-filelock)

## slackapi
Used in: slack_report.py

[slackapi github](https://github.com/slackapi/python-slackclient)

## copy
Used in: utils.py

[copy docs](https://docs.python.org/3/library/copy.html)

# CI libraries references

- [nox](https://nox.thea.codes/en/stable/)
- [mypy](http://mypy-lang.org/)
- [pylint](https://github.com/PyCQA/pylint)
- [isort](https://pycqa.github.io/isort/)
- [black](https://github.com/psf/black)
- [bandit](https://bandit.readthedocs.io/en/latest/)
- [pyreverse](https://pythonhosted.org/theape/documentation/developer/explorations/explore_graphs/explore_pyreverse.html)