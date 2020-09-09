# Setting up the environment
The project runs with Python>3.8

[//comment]: # (TODO: This is the correct python version?)

To install the dependencies in [editable mode](https://pip.pypa.io/en/stable/reference/pip_install/#install-editable)
in the root of the project run:

```bash
pip install -e .
```

This will install the package in
[development mode](https://setuptools.readthedocs.io/en/latest/setuptools.html#develop-deploy-the-project-source-in-development-mode).

[//comment]: # (TODO: We could use some dependency manager)
[//comment]: # (https://packaging.python.org/tutorials/managing-dependencies/#other-tools-for-application-dependency-management)

In a temporary test folder using the same interpreter make a smoke test running:
```bash
soam init --output
```
That should create the scaffold for a new project.