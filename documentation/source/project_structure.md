# Directory structure

## root
### [gitignore](../../.gitignore)
This [description file](https://git-scm.com/docs/gitignore) specifies the excluded documents and folders from git.

### [README](../../README.md)
This document contains a brief overview of the project working and how to use it, it's oriented to the users of the
package.

### [setup.py](../../setup.py)
This [configuration file](https://packaging.python.org/guides/distributing-packages-using-setuptools/#setup-py)
determines how the SoaM package is going to be installed and what commands it supports.

### [setup.cfg](../../setup.cfg)
This [ini file](https://packaging.python.org/guides/distributing-packages-using-setuptools/#setup-cfg) defines default
options for the setup.py commands.

## documentation
Contains the technical documentation for the project, it's oriented to the development team.

### images
The diagrams and visualizations for the documentation.

### [classes](classes.md)
Explanation and diagrams of the classes and patterns in the project.

### [developers starting point](developers_starting_point.md)
Steps description to setup the project for development. If you are new in SoaM this is your next document in your path
to start developing.

### project structure
This document :D

### [references](references.md)
Papers, articles and videos to understand the theoretical background, libraries and technologies used in the project.

[//comment]: # (TODO: ### architecture)
[//comment]: # (TODO: create some expected or possible architecture implementations.)

## notebook
There are different proof of concepts, tests and usage examples.

## soam
The root of the source code for the project.

### db_migrations
This directory contains the migrations for the database that stores the data and runs with the DBSaver.

### [alembic.ini](../../soam/alembic.ini)
Configures the alembic library to manage the migrations for the DBSaver.

### templates
Contains the directory structure that cookiecutter is going to generate.

### resources
Files that will be used in the pipeline, like a template for an email report in a postprocess step.

[//comment]: # (TODO: review if this directory is outdated or not used any more.)
