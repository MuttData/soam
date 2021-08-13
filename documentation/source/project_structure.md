# Directory structure

## root
### [gitignore](https://gitlab.com/mutt_data/soam/-/blob/master/.gitignore)
This [description file](https://git-scm.com/docs/gitignore) specifies the excluded documents and folders from git.

### [README](./README.html)
This document contains a brief overview of the project working and how to use it, it's oriented to the users of the
package.

### [setup.py](https://gitlab.com/mutt_data/soam/-/blob/master/setup.py)
This [configuration file](https://packaging.python.org/guides/distributing-packages-using-setuptools/#setup-py)
determines how the SoaM package is going to be installed and what commands it supports.

### [setup.cfg](https://gitlab.com/mutt_data/soam/-/blob/master/setup.cfg)
This [ini file](https://packaging.python.org/guides/distributing-packages-using-setuptools/#setup-cfg) defines default
options for the setup.py commands.

## [documentation](./development_pipeline.html#documentation)
Contains the technical documentation for the project, it's oriented to the development team.

### [images](https://gitlab.com/mutt_data/soam/-/tree/master/documentation/images)
The diagrams and visualizations for the documentation.

### [classes](./classes.html)
Explanation and diagrams of the classes and patterns in the project.

### [developers starting point](./developers_starting_point.html)
Steps description to setup the project for development. If you are new in SoaM this is your next document in your path
to start developing.

### project structure
This document :D

### [references](./references.html)
Papers, articles and videos to understand the theoretical background, libraries and technologies used in the project.

[//comment]: # (TODO: ### architecture)
[//comment]: # (TODO: create some expected or possible architecture implementations.)

## [notebook](https://gitlab.com/mutt_data/soam/-/tree/master/notebook)
There are different proof of concepts, tests and usage examples.

## [soam](https://gitlab.com/mutt_data/soam/-/tree/master/soam)
The root of the source code for the project.

### [db_migrations](https://gitlab.com/mutt_data/soam/-/tree/master/soam/db_migrations)
This directory contains the migrations for the database that stores the data and runs with the DBSaver.

### [alembic.ini](https://gitlab.com/mutt_data/soam/-/blob/master/soam/alembic.ini)
Configures the alembic library to manage the migrations for the DBSaver.

### [resources](https://gitlab.com/mutt_data/soam/-/tree/master/soam/resources)
Files that will be used in the pipeline, like a template for an email report in a postprocess step.

[//comment]: # (TODO: review if this directory is outdated or not used any more.)
