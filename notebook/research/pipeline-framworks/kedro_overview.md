# Kedro overview

In this document will show the overview of [Kedro](https://kedro.readthedocs.io).

Kedro is an open-source Python framework for data and machine-learning pipelines.

## Install
check  [prerequisites](https://kedro.readthedocs.io/en/stable/02_get_started/01_prerequisites.html#virtual-environments)

for installation use conda:
```bash
conda install -c conda-forge kedro
```
also can be installed with pip:
```bash
pip install "kedro[all]"
```

for all the dependencies or define which dependencies you want to install


```bash
!kedro info
```
     _            _
    | | _____  __| |_ __ ___
    | |/ / _ \/ _` | '__/ _ \
    |   <  __/ (_| | | | (_) |
    |_|\_\___|\__,_|_|  \___/
    v0.16.4

    kedro allows teams to create analytics
    projects. It is developed as part of
    the Kedro initiative at QuantumBlack.

    No plugins installed


## Project Template
Kedro provides a standard, modifiable and easy-to-use project template based on [Cookiecutter Data Science](https://github.com/drivendata/cookiecutter-data-science/).
```bash
kedro new project-name
```
```
project-name
├── conf
│   ├── base
│   │   ├── catalog.yml
│   │   ├── credentials.yml
│   │   ├── logging.yml
│   │   └── parameters.yml
│   └── local
├── data
│   └── 01_raw
│       └── iris.csv
├── docs
│   └── source
│       ├── conf.py
│       └── index.rst
├── kedro_cli.py
├── logs
│   ├── info.log
│   └── journals
│       └── journal_2020-08-19T14.36.39.421Z.json
├── notebooks
├── README.md
├── setup.cfg
└── src
    ├── project-name
    │   ├── pipeline.py
    │   ├── pipelines
    │   │   ├── data_science
    │   │   │   ├── nodes.py
    │   │   │   ├── pipeline.py
    │   │   │   └── README.md
    │   └── run.py
    ├── requirements.txt
    └── setup.py
```

And it will ask your for the project name and create a project template for you with configs files, a CLI done with click.

## ProjectContext
Project context is the base configuration for the pipeline, where you register the hooks for example or configure the logging.

## Data Catalog
Kedro has a series of data connectors used for saving and loading data across many different file formats and file systems including local and network file systems, cloud object stores, Pickle, Parquet, SQL db and HDFS.

The Data Catalog also includes data and model versioning for file-based systems.

Used with a Python or YAML API. For this example we will use the Python API

```bash
!wget https://raw.githubusercontent.com/facebook/prophet/master/examples/example_retail_sales.csv
```

```python
from kedro.io import DataCatalog, MemoryDataSet
from kedro.extras.datasets.pandas import CSVDataSet

data_catalog = DataCatalog(
    {
        "retail": CSVDataSet(filepath="./example_retail_sales.csv")
    }
)
retail_df = data_catalog.load("retail")
retail_df.tail()
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>ds</th>
      <th>y</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>288</th>
      <td>2016-01-01</td>
      <td>400928</td>
    </tr>
    <tr>
      <th>289</th>
      <td>2016-02-01</td>
      <td>413554</td>
    </tr>
    <tr>
      <th>290</th>
      <td>2016-03-01</td>
      <td>460093</td>
    </tr>
    <tr>
      <th>291</th>
      <td>2016-04-01</td>
      <td>450935</td>
    </tr>
    <tr>
      <th>292</th>
      <td>2016-05-01</td>
      <td>471421</td>
    </tr>
  </tbody>
</table>
</div>

### in-memory dataset

```python
memory_data = MemoryDataSet(data=retail_df)
loaded_mem = memory_data.load()
loaded_mem.tail()
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>ds</th>
      <th>y</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>288</th>
      <td>2016-01-01</td>
      <td>400928</td>
    </tr>
    <tr>
      <th>289</th>
      <td>2016-02-01</td>
      <td>413554</td>
    </tr>
    <tr>
      <th>290</th>
      <td>2016-03-01</td>
      <td>460093</td>
    </tr>
    <tr>
      <th>291</th>
      <td>2016-04-01</td>
      <td>450935</td>
    </tr>
    <tr>
      <th>292</th>
      <td>2016-05-01</td>
      <td>471421</td>
    </tr>
  </tbody>
</table>
</div>

### Partitioned dataset
Loads and saves partitioned file-like data using the underlying dataset definition.
No db nor a DataFrame

## Pipeline abstraction
Kedro is based on a Pipeline and node objects to run.

Here is a simple Kedro Pipeline.


```python
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import node, Pipeline
from kedro.runner import SequentialRunner

# Prepare a data catalog
data_catalog = DataCatalog({"example_data": MemoryDataSet()})


def return_greeting():
    # Prepare first node
    return "Hello"


return_greeting_node = node(return_greeting, inputs=None, outputs="my_salutation")

def join_statements(greeting):
    # Prepare second node
    return f"{greeting} Kedro!"

join_statements_node = node(join_statements, inputs="my_salutation", outputs="my_message")

# Assemble nodes into a pipeline
pipeline = Pipeline([return_greeting_node, join_statements_node])

# Create a runner
runner = SequentialRunner()

# Run the pipeline
runner.run(pipeline, data_catalog)
```
    {'my_message': 'Hello Kedro!'}



## Runner
As you can see in the above example you define a runner and provide a pipeline and a datacatalog to run.

There are 3 defined Runners:
* `SequentialRunner`
* `ParallelRunner`
* `ThreadRunner`

There is no `Dask` or other runners implementations

You can run with the Python or with CLI :
```bash
kedro run
```
In the project file

## Hooks
Hooks are a mechanism to add extra behavior to Kedro’s main execution in an easy and consistent manner.
In the [hooks-tutorial](https://github.com/quantumblacklabs/kedro-examples/tree/master/kedro-hooks-tutorial) they made 3 examples:
* Data validation with `Great Expectations`.
* Pipeline observability visualize using `Grafana`.
* Metrics tracking with `MLflow`.

There are diferents types of hooks:
* [after|before]_[node|pipeline]_run
* on_[node|pipeline]_error
* after_catalog_created


```python
class ModelTrackingHooks:
    """Namespace for grouping all model-tracking hooks with MLflow together.
    """

    @hook_impl
    def before_pipeline_run(self, run_params: Dict[str, Any]) -> None:
        """Hook implementation to start an MLflow run
        with the same run_id as the Kedro pipeline run.
        """
        mlflow.start_run(run_name=run_params["run_id"])
        mlflow.log_params(run_params)

    @hook_impl
    def after_node_run(
        self, node: Node, outputs: Dict[str, Any], inputs: Dict[str, Any]
    ) -> None:
        """Hook implementation to add model tracking after some node runs.
        In this example, we will:
        * Log the parameters after the data splitting node runs.
        * Log the model after the model training node runs.
        * Log the model's metrics after the model evaluating node runs.
        """
        if node._func_name == "split_data":
            mlflow.log_params(
                {"split_data_ratio": inputs["params:example_test_data_ratio"]}
            )

        elif node._func_name == "train_model":
            model = outputs["example_model"]
            mlflow.sklearn.log_model(model, "model")
            mlflow.log_params(inputs["parameters"])

    @hook_impl
    def after_pipeline_run(self) -> None:
        """Hook implementation to end the MLflow run
        after the Kedro pipeline finishes.
        """
        mlflow.end_run()
```

## Run versioning / Jorunal
Journal in Kedro allows you to save the history of pipeline.
Each pipeline run creates a log file formatted as `journal_YYYY-MM-DDThh.mm.ss.sssZ.log`, which is saved in the logs/journals directory.
The log file contains two kinds of journal records.

### Context journal record
A context journal record captures all the necessary information to reproduce the pipeline run, and has the following JSON format

### Dataset journal record
A dataset journal record tracks versioned dataset load and save operations, it is tied to the dataset name and `run_id`.

While the context journal record is always logged at every run time of your pipeline, dataset journal record is only logged when load or save method is invoked for versioned dataset in DataCatalog. This are the file-like Datasets

Didn't find a proper way to setup the `Journal`

## Debugging
Kedro can be debugged with an IDE and it example how to set it up.

If not you can add a Hook on_[node|pipe]_error and implement an error Hook with `pdb` or `ipdb`.

Here is an example on how to use it:

```python
import pdb
import sys
import traceback

from kedro.framework.hooks import hook_impl

class PDBNodeDebugHook:
    """A hook class for creating a post mortem debugging with the PDB debugger
    whenever an error is triggered within a node. The local scope from when the
    exception occured is available within this debugging session.
    """

    @hook_impl
    def on_node_error(self):
        _, _, traceback_object = sys.exc_info()

        #  Print the traceback information for debugging ease
        traceback.print_tb(traceback_object)

        # Drop you into a post mortem debugging session
        pdb.post_mortem(traceback_object)
```

Remember that every hook must be registered in the ProjectContext

```python
class ProjectContext(KedroContext):
    hooks = (PDBNodeDebugHook(),)
```

## UI
For the UI kedro add a plugin [Kedro-Viz](https://github.com/quantumblacklabs/kedro-viz), a tool for visualizing your Kedro pipelines

![kedro-viz](https://raw.githubusercontent.com/quantumblacklabs/kedro-viz/develop/.github/img/pipeline_visualisation.png)

## Extras
* [Kedro-Docker](https://github.com/quantumblacklabs/kedro-docker): a tool for packaging and shipping Kedro projects within containers
* [Kedro-Airflow](https://github.com/quantumblacklabs/kedro-airflow): a tool for converting your Kedro project into an Airflow project
* [Kedro-Pandas-Profiling](https://github.com/BrickFrog/kedro-pandas-profiling) : A simple wrapper to use Pandas Profiling easily in Kedro
* `Jupyter`: Kedro brings a jupyter notebook installed, just running kedro jupyter notebook will start a jupyter server and see the files in the notebook folder
