# SoaM

[![pipeline status](https://gitlab.com/mutt_data/soam/badges/master/pipeline.svg)](https://gitlab.com/mutt_data/soam/-/commits/master) [![coverage report](https://gitlab.com/mutt_data/soam/badges/master/coverage.svg)](https://gitlab.com/mutt_data/soam/-/commits/master) [![pypi version](https://img.shields.io/pypi/v/soam?color=blue)](https://pypi.org/project/soam/)

SoaM is library created by [Mutt](https://muttdata.ai/).
Its goal is to create a forecasting framework, this tool is developed with conjunctions of experience on previous
projects. There come the name: Son of a Mutt = SoaM

## SoaM pipeline

```mermaid

   graph LR
    id0[(Database I)]-->id2[/SoaM Time Series Extractor/]
    id1[(Database II)]-->id2
    id2-->id3[/SoaM Transformer/]
    id3-->id4[/SoaM Forecaster/]
    id5{{Forecasting Model}}-->id4
    id4-->id6[(SoaM Predictions)]
    id6-->id7[/SoaM Forecaster Plotter/]
    id6-->id8[/SoaM Reporting/]
    id7-->id8
```

This library pipeline supports any data source.
The process is structured in different stages:
* Extraction: manages the granularity and aggregation of the input data.
* Preprocessing: lets select among out of the box tools to perform standard tasks as normalization or fill nan values.
* Forecasting: fits a model and predict results.
* Postprocessing: modifies the results based on business/real information or create analysis with the predicted values,
 such as an anomaly detection.

## Overview of the Steps Run in SoaM (planned)

### Extraction
This stage extracts data from the needed sources to build the condensed dataset for the next steps. This tends to be
project dependent. Then it converts the full dataset to the desired time granularity and aggregation level by some categorical attribute/s.

### Preprocessing
This step implements functions to further cleanup and prepare the data for the following steps, such as:
* Add feature/transformation
* Fill nan values
* Apply value normalizations
* Shift values

[//comment]: # (the preprocessing supports custom transformations?)

### Forecasting
This stage receives the clean data, performs the forecast and store the predicted values in the defined storages.
Currently there are implementations to store in CSV files and SQL databases.
A variety of models are currently supported to fit and predict data. They can be extended to create custom ones.
* [Exponential Smoothing](https://www.statsmodels.org/stable/examples/notebooks/generated/exponential_smoothing.html)
* [Orbit DLT Full](https://orbit-ml.readthedocs.io/en/latest/tutorials/dlt.html)
* [Prophet](https://pypi.org/project/fbprophet)
* [SARIMAX](https://www.statsmodels.org/dev/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html)

### Postprocessing
[//comment]: # (TODO: explain postprocessing stage chaining)
This last stage is prepared to work on the forecasts generated by the pipeline. For example:
* Clip/Cleanup the predictions.
* Perform further analyses (such as anomaly detection).
* Export reports.

[//comment]: # (does the postprocessing support custom outputs?)

## Table of Contents
- [Installation](#installation)
- [Quick start](#quick-start)
- [Usage](#usage)
- [Soam CLI](#soam-cli)
- [Database Management](#database-management)
- [Developers Guide](#developers-guide)
- [Testing](#testing)
- [Contributing](#contributing)
- [Rules of Thumb](#rules-of-thumb)
- [Credits](#contributing)
- [License](#license)

## Installation
Install the base lib via [pipy](https://pypi.org/project/soam/) by executing:
```bash
pip install soam
```
Or clone this repository:
```bash
git clone [soam-repo]
```
And then run:
```bash
pip install . or pip install -e .
```

### Install extras
The project contains some extra dependencies that are not included in the default installation to make it lightweight. If you want to install extensions use:
```bash
pip install -e ".[slack]"
pip install -e ".[prophet]"
pip install -e ".[pdf_report]"
pip install -e ".[gsheets_report]"
pip install -e ".[report]" # slack and *_report extras
pip install -e ".[all]" # all previous
```

_Note_: The `pdf_report` extra might need to run the following command before installation ([More info](https://nbconvert.readthedocs.io/en/latest/install.html#installing-tex))

  $ `apt-get install texlive-xetex texlive-fonts-recommended libpoppler-cpp-dev`

## Quick start
[Here](quickstart.ipynb) is an example for a quick start into SoaM. In it a time series with AAPL stock prices is loaded, processed and forecasted. As well, there's [other example](soamflowrun.ipynb) with the same steps, but exploding the power of flows.

## Usage
For further info check our **[end to end](end2end.md)** example where we explained how SoaM will interact with Airflow on a generic project.

## Database management
For database storing there are complementary tools:
* [muttlib.dbcon](https://gitlab.com/mutt_data/muttlib/) for database connections.
* [Decouple](https://github.com/henriquebastos/python-decouple) storing the database information in a separated file.  With a [settings.ini](soam/settings.ini) file to store the database credentials and general configurations, when modifying it don't change the keys names.
* [Alembic](https://alembic.sqlalchemy.org/en/latest/) to create the database migrations. A brief description is below.
* [SQLAlchemy](https://docs.sqlalchemy.org/en/) as an ORM, the schemas of the tables are defined in[data_models](soam/data_models.py).

### Alembic
This package uses alembic and expects you to use it!

Alembic is a database migration tool for usage with SQLAlchemy.
After defining the schemas, with SQLAlchemy, Alembic keeps track of the database modifications such as add new
columns, modify a schema or add new tables.

Alembic is set up to use the credentials from the `settings.ini` file and get the defined models from `data_models`.
Be aware that alembic needs this package installed to run!

When making any change of the data models you need them to impact into the database for this you will have to run:

```bash
alembic revision --autogenerate
alembic upgrade head
```

The first command will check the last version of the database and will
[autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect)
the python file with the necessary changes.
It is always necessary to manually review and correct the candidate migrations that autogenerate produces.

The second command will use this file to impact the changes in the database.

For more alembic commands visit the [documentation](https://alembic.sqlalchemy.org/en/latest/)

[//comment]: # (TODO: add documentation about parameter and step logging.)
[//comment]: # (TODO: split and reorder documentation.)


## Developers guide
If you are going to develop SoaM, you should checkout the documentation directory before adding code,
you can start in the [project structure document](documentation/source/project_structure.md).

## Testing
To run the default testsuite run this:
```
pytest
```
To run the tests with nox:
```bash
nox --session tests
```

### Testing data extraction
The tests for the extractor currently depends on having a local Postgres database and
the variable `TEST_DB_CONNSTR` set with it's connection string.

The easiest way to to this is as follows:
```
docker run --network=host \
    -e "POSTGRES_USER=soam" \
    -e "POSTGRES_PASSWORD=soam" \
    -e "POSTGRES_DB=soam" \
    --rm postgres

TEST_DB_CONNSTR="postgresql://soam:soam@localhost/soam" pytest
```

To run a specific test file:
```bash
TEST_DB_CONNSTR="postgresql://soam:soam@localhost/soam" pytest -v tests/test_file.py
```

Note that even though the example has a DB name during the tests a new database is created and dropped to ensure that no state is maintened between runs.


### Testing plots
To generate images for testing we use [pytest-mpl](https://github.com/matplotlib/pytest-mpl) as follows:

```
pytest --mpl-generate-path=tests/plotting/baseline
```

To run the image based tests:
```
pytest --mpl
```

## Contributing
We appreciate for considering to help out maintaining this project. If you'd like to contribute please read our [contributing guidelines](CONTRIBUTING.md).

## Rules of Thumb
This section contains some recommendations when working with SoaM to avoid common mistakes:

* When possible reuse objects to preserve their configuration.
  Eg: Transformations, forecasters, etc.
* Use the same train-test windows when backtesting and training to deploy and on later usage.

## Credits
Alejandro Rusi <br>
Diego Lizondo <br>
Eugenio Scafati <br>
Fabian Wolfmann <br>
Francisco Lopez Destain <br>
Guido Trucco <br>
Juan Martin Pampliega <br>
Pablo Andres Lorenzatto <br>
Wenceslao Villegas

## License
`soam` is licensed under the [Apache License 2.0](https://gitlab.com/mutt_data/muttlib/-/blob/master/LICENCE).
