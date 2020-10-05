# Sprints and tasks
[//comment]: # (TODO: Explain how we are using gitlab boards)
[//comment]: # (TODO: Link or explain the worklow to solver issues)

# Debugging
[//comment]: # (TODO: Explain the setup to debug the project)


# CI

To run the CI jobs locally you have to run it with [nox](https://nox.thea.codes/en/stable/):
In the project root directory, there is a noxfile.py file defining all the jobs, these jobs will be executed when calling from CI or you can call them locally.

You can run all the jobs with the command `nox`, from the project root directory or run just one job with `nox --session test` command, for example.

[//comment]: # (TODO: Link or explain how to run test and check locally)
[//comment]: # (TODO: Review the following CI explanation)

The .gitlab-ci.yml file configures the gitlab CI to run nox.
Nox let us execute some test and checks before making the commit.
We are using:
* Linting job:
    * isort to reorder imports
    * pylint to be pep8 compliant
    * black to format for code conventions
    * mypy for static type checking
* Bandit for security checks
* Pytests to run all the tests in the test folder.
* Pyreverse to create diagrams of the project

This runs on a gitlab machine after every commit.

We are caching the environments for each job on each branch.
On every first commit of a branch, you will have to change the policy also if you add dependencies or a new package to the project.
Gitlab cache policy:
* `pull`: pull the cached files from the cloud.
* `push`: push the created files to the cloud.
* `pull-push`: pull the cached files and push the newly created files.
