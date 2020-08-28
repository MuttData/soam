
# {{ cookiecutter.project_name }} by {{ cookiecutter.author_name }}

{{ cookiecutter.description }}

# Directory structure of generated projects

```
├── bandit.yaml                         # Bandit security linter config file.
├── .bump                               # Version bump file.
├── CHANGELOG.md                        # Documentation of notables changed made to the project.
├── CONTRIBUTING.md                     # Contributing guidelines.
├── {{ cookiecutter.project_name }}     # Source code directory.
│   ├── alembic.ini                     # Alembic database migration config file.
│   ├── cfg.py                          # Parses/loads the `settings.ini` file, defaults to `constants.py`
│   ├── constants.py                    # Constant values and defaults used in multiple modules.
│   ├── dags                            # Dir for Airflow DAGs.
│   │   └── main_dag.py                 # Main DAG to run the project.
│   ├── db_models.py                    # Database models.
│   ├── helpers.py                      # Project dependant helper code.
│   ├── main.py                         # Main entry-point for the project.
│   ├── resources                       # Dir for .j2, .sql and other non Python files used mostly inside Python.
.
│   ├── settings_sample.ini             # Sample settings file, should be copied into settings.ini and NEVER pushed!
.
│   └── utils.py                        # Project agnostic helper functions that could be migrated to and external lib.
├── .coveragerc                         # Code coverage config file.
├── Dockerfile                          # Build the project's main image.
├── docs                                # Folder for storing the project's documentation.
│   └── ...
├── .flake8                             # Flake8 sample config file.
├── .gitignore                          # .gitignore with sensible defaults
├── .gitlab-ci.yml                      # .gitlab-ci.yml, for running tests on Gitlab CI/CD
├── mypy.ini                            # mypy config file
├── notebooks                           # Directory for storing Jupyter-Notebooks
│   └── ...                             #
├── noxfile.py                          # Noxfile config file.
├── .pre-commit-config.yaml             # Pre-Commit hooks.
├── pylintrc                            # Pylint config file.
├── pyproject.toml                      # pyproject config file, with settings for build and black.
├── README.md                           # This file.
├── requirements.txt                    # Requirements for building this project.
├── setup.cfg                           # Setup config.
└── tests                               # Directory for storing tests.
```

# Running the project

*TODO*

# Docker stuff

Build main image.

```
docker build . -t {{ cookiecutter.project_name }}
```
