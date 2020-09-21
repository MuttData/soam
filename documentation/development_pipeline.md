# Sprints and tasks
[//comment]: # (TODO: Explain how we are using gitlab boards)
[//comment]: # (TODO: Link or explain the worklow to solver issues)

# Debugging
[//comment]: # (TODO: Explain the setup to debug the project)


# CI

[//comment]: # (TODO: Link or explain how to run test and check locally)
[//comment]: # (TODO: Review the followin CI explanation)

The .gitlab-ci.yml file configures the gitlab CI to run nox.
Nox let us execute some test and checks before making the commit.
We are using:
 * isort to reorder imports
 * bandit for security checks
 * pylint to be pep8 compliant
 * black to format for code conventions
 * mypy for static type checking

This runs on a gitlab machine after every commit.

We are also running pyreverse to create diagrams for the project.