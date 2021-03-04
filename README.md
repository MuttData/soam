# SoaM

SoaM is library created by [Mutt](https://muttdata.ai/).
Its goal is to create a forecasting framework, this tool is developed with conjunctions of experience on previous
projects. There come the name: Son of a Mutt = SoaM

## SoaM pipeline


![soam_pipeline](documentation/images/SoaM_diagram.png)

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
project dependent.

Then it converts the full dataset to the desired time granularity and aggregation level by some categorical attribute/s.

### Preprocessing
This step implements functions to further cleanup and prepare the data for the following steps.

Such as:
* Add feature/transformation
* Fill nan values
* Apply value normalizations
* Shift values

[//comment]: # (the preprocessing supports custom transformations?)

### Forecasting
This stage receives the clean data, performs the forecast and store the predicted values in the defined storages.
Currently there are implementations to store in CSV files and SQL databases.

We use [Darts](https://github.com/unit8co/darts) models to fit and predict data.
They can be extended to create custom ones.

[//comment]: # (TODO: add some description to the diagram)

### Postprocessing
This last stage or stages is prepared to work on the forecasts generated by the pipeline.

[//comment]: # (TODO: explain postprocessing stage chaining)

for example to
* Clip/Cleanup the predictions
* Perform further analyses (such as anomaly detection)
* Export reports

[//comment]: # (the postprocessing supports custom outputs?)

# Install extras

The project contains some extra dependencies that are not included in the default installation to make it lightweight.

If you want slack or prophet extensions use:
```bash
pip install -e ".[slack]"
pip install -e ".[prophet]"
pip install -e ".[pdf_report]"
```

_Note_: The `pdf_report` extra might need to run the following command before installation

  $ `apt-get install texlive-xetex texlive-fonts-recommended`

## Examples

* Forecaster : here is a [notebook](./notebook/examples/forecaster.ipynb) using and explaining the forecaster stage.

[//comment]: # (this can be a more accurate example in a separated repository)

## SoaM CLI

After installing SoaM locally (for example with `pip install soam`), there are some commands available:

* `soam init --output`, scaffolding for a project ready to use SoaM. `cookiecutter` will then ask for parameters via prompt.

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

## Rules of Thumb

This section contains some recommendations when working with SoaM to avoid common mistakes:

* When possible reuse objects to preserve their configuration.
  Eg: Transformations, forecasters, etc.
* Use the same train-test windows when backtesting and training to deploy and on later usage.

