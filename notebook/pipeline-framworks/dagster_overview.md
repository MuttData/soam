# Dagster overview

In this document will show the overview of [Dagster](https://docs.dagster.io/).

Dagster is an open-source Python framework for data orchestrator in machine learning, analytics, and ETL.

## Overview
Don't have project template, you have to make it yourself from the examples. 
Eery object is instanced with a decorator. 

Configuration and definitions have to be in a yaml file.

Not a pretty good CLI, it does have a good API, the documentation is not very good explained.

Very tied to de UI.

## Install
For installation use pip:
```bash
pip install dagster dagit
```
Will install the base of Dagster and the UI (Dagit).
If you want to add, for example, a celery executor you will need to install it.
```bash
pip install dagster-celery
```

```bash
dagster --version
```
    dagster, version 0.9.2

While whe write this overview Dagster is on version 0.9.2

## Project Template 
Dagster doesn't provide a project template like `cookiecutter` or other, but it is on their issues to address.

Dagster contains a CLI done with click. Very basic with a few commands.

## Context
The context of the run, each solid need the context at the construction.
It contains the context data for logging, storing, debugging, etc.

## Pipeline abstraction
Dagster is based on a Pipeline and Solid objects to run. 
The Dagster objects are defined with decorators, to define a resource, solid or pipeline. 

Here is a simple Dagster Pipeline.

```python
from dagster import (
    InputDefinition,
    Output,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    solid,
)


@solid(output_defs=[OutputDefinition(name="greeting", dagster_type=str)])
def hello_world(context):
    yield Output("Hello", output_name="greeting")


@solid(input_defs=[InputDefinition("greeting", str)],)
def salutation(context, greeting):
    return f"{greeting} Dagster!"


@pipeline
def serial_pipeline():
    greeting = salutation(hello_world())
    print(greeting)


execute_pipeline(serial_pipeline)
```

Dependencies between solids in Dagster are defined using `InputDefinitions` and `OutputDefinitions`

With Solids you can return more than one thing, yielding more than one Output, an ExpectationResult (they have their own expectations), Failure, and [others](https://docs.dagster.io/overview/solids-pipelines/solid-events). 

You can customize a [solid definition](https://docs.dagster.io/overview/solids-pipelines/solid-factories) 

## Run 
You can run a pipeline in diferent ways:
* CLI: 
    ```bash
    dagster pipeline execute -f hello_cereal.py
    ```
    With `-f` define the file where its the pipeline, or you can use `-p` and define the name of the pipeline
* Python API: 
    ```python
    execute_pipeline(serial_pipeline)
    ```
    This way you will execute the pipeline and you can add configurations and modes to run it. 
* From the GUI in the `Dagit` tool

## Partitions and Backfills
Dagster provides the partition set abstraction to make it easy to partition config for a pipeline.

After defining a partition set, you can use backfills to instigate pipeline runs for each partition or subsets of partitions of the partition set.

## Executors
Executors are responsible for executing steps within a pipeline run.

There are several defined Executors:
* `Celery`
* `Dask`
* `K8S`
* `in process`
* `multi process`

## Run versioning 
For storing each run dagster provides a feature to save in a database (SQLite or Postgres). 
It also can store event logs, compute logs, and others elements.

For storing each solid run you may log what you want.

It can easily persist the output of each solid in a persistent manner,
just defining a storage in the configuration file.

I try this as its documented but no log record was generated.

## Debugging
For debugging the docs page suggest to debug with logs and the UI.

## Configuration
You can define a configurable parameters to run your pipeline with `run_config`. 
You can configure:
* execution: Determine and configure the Executor.
* storage: Define how data between solid will be persisted.
* loggers :Provide values for solid specific configuration.
* resources : Configure resources that belong to the pipeline that have defined configuration schema.

```python
@solid(
    config_schema={
        # can just use the expected type as short hand
        'iterations': int,
        # otherwise use Field for optionality, defaults, and descriptions
        'word': Field(str, is_required=False, default_value='hello'),
    }
)
def config_example_solid(context):
    for _ in range(context.solid_config['iterations']):
        context.log.info(context.solid_config['word'])

@pipeline
def config_example_pipeline():
    config_example_solid()

def run_config_example():
    return execute_pipeline(
        config_example_pipeline,
        run_config={'solids': {'config_example_solid': {'config': {'iterations': 1}}}},
    )
```

## Modes and Resources
Modes and resources provide a way to control the behavior of multiple solids at pipeline execution time. 
A typical usage for modes is to vary pipeline behavior between different deployment environments. 

```python
@pipeline(
    mode_defs=[
        ModeDefinition('local_dev', resource_defs={'database': sqlite_database}),
        ModeDefinition('prod', resource_defs={'database': postgres_database}),
    ],
)
def generate_tables_pipeline():
    generate_table_1()
    generate_table_2()
```

and for executing :
```bash
dagster pipeline execute -d local_dev generate_tables_pipeline
```

## UI
For the UI Dagster has Dagit, very useful UI. 
You can run the pipeline, see the historical runs, run a part of the pipeline, see errors and more.

![Dagit](https://docs.dagster.io/assets/images/tutorial/serial_pipeline_figure_one.png)

## Extras
* Expectations: Assert datatypes and business logic.
* Repository: Is a list of pipelines to execute.
* Cloud support: Support AWS(S3, Redshift and CloudWatch), Azure (Azure Data Lake and Blob storage), GCP (Bigquery and GCS)
* dagstermill: Wraps Jupyter notebooks as solids to enable repeatable execution integrated into  Dagster pipelines. Built on papermill
* Airflow: Crete airflow DAG from pipeline.
