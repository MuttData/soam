# Setting up the environment
The project runs with Python>=3.6

To install the dependencies in [editable mode](https://pip.pypa.io/en/stable/reference/pip_install/#install-editable)
in the root of the project run:

```bash
pip install -e ".[dev]"
pip install -e ".[test]"
```

[//comment]: # (TODO: 'python setup.py develop' is not working, should be the same as 'pip install -e .')
[//comment]: # (TODO: 'python setup.py develop' is failing to obtain muttlib.)

This will install the package in
[development mode](https://setuptools.readthedocs.io/en/latest/setuptools.html#develop-deploy-the-project-source-in-development-mode).

[//comment]: # (TODO: We could use some dependency manager)
[//comment]: # (https://packaging.python.org/tutorials/managing-dependencies/#other-tools-for-application-dependency-management)

In a temporary test folder using the same interpreter make a smoke test running:
```bash
soam init --output
```
That should create the scaffold for a new project.

Check that you have an up to date muttlib version or upgrade it:
```bash
pip install --upgrade git+https://gitlab.com/mutt_data/muttlib#egg=muttlib
```
[//comment]: # (TODO: Include what version we are using.)

# Next Steps
* If you already have the project running the last step before making your first commit is to review the
[development pipeline](development_pipeline.md).
* If you want more information about the main classes or patterns in the project go to [classes document](classes.md).
* If you need to understand a library, technology or concept in the project you can check the
[references](references.md).

