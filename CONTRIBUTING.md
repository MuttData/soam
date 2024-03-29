# Contributing to SoaM
Thanks for your interest in contributing to SoaM 🎉. These are the guidelines for contributions. Reading them will help you get started on how to make useful contributions.

## Foreword
This guide is not final. It will evolve over time, as we learn and add new voices to the project. Check it from time to time and feel free to make suggestions 😃

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Issues](#issues)
  - [Labels](#labels)
  - [Security issues](#security-issues)
- [Development Setup](#development-setup)
  - [Installation](#installation)
  - [Pre-Commit for Version Control Integration](#pre-commit-for-version-control-integration)
- [Style guide](#style-guide)
- [Docstrings](#docstrings)
- [Testing](#testing)
  - [Regression testing](#regression-testing)
- [Documentation](#documentation)
- [Versioning](#versioning)
- [Deprecation](#deprecation)
  - [Decorator](#decorator)
  - [Release](#release)
- [PRs](#prs)
  - [WIP](#wip)
  - [RFC](#rfc)
  - [CI/CD jobs](#cicd-jobs)
- [Rules of Thumb](#rules-of-thumb)

## Code of Conduct
One of our core values at Mutt is that **we are an open team**. We all make mistakes and need help fixing them. We foster psychological safety. We clearly express it when we don’t know something and ask for advice.

We expect everyone contributing to SoaM to follow this principle. Be kind, don't be rude, keep it friendly; learn, teach, ask and help.

## Issues

Before submitting an issue, first check on the [issues tracker](https://gitlab.com/mutt_data/soam/issues) if there is already one trying to cover that topic, to avoid duplicates. Otherwise we invite you to create it. And if you feel that your issue can be categorized you can use this labels:

### Labels

| name | description | shortcuts |
| ---------- | ----------- | ------ |
| `bug` | Report a bug | [Look](https://gitlab.com/mutt_data/soam/issues?scope=all&utf8=✓&state=opened&label_name[]=bug) for `bug` or [create](https://gitlab.com/mutt_data/soam/-/issues/new?issuable_template=Bug) one
|`feature-request`|Request for a new feature|[Look](https://gitlab.com/mutt_data/soam/issues?scope=all&utf8=✓&state=opened&label_name[]=feature-request) for `feature-request` or [create](https://gitlab.com/mutt_data/soam/-/issues/new?issuable_template=Feature) one
|`enhancement`|Propose an enhancement|[Look](https://gitlab.com/mutt_data/soam/issues?scope=all&utf8=✓&state=opened&label_name[]=enhancement) for `enhancement` or [create](https://gitlab.com/mutt_data/soam/-/issues/new?issuable_template=Enhancement) one
|`discussion`|Start a new discussion|[Look](https://gitlab.com/mutt_data/soam/issues?scope=all&utf8=✓&state=opened&label_name[]=discussion) for `discussion` or [create](https://gitlab.com/mutt_data/soam/-/issues/new?issuable_template=Discussion) one

### Security issues
If you find a security related bug or any kind of security rellated issue, **please DO NOT file a public issue**. Sensitive security-related issues should be reported to privately to the repo owner along with a PoC if possible. You can [send us an email](mailto:security@muttdata.ai) and we'll go from there.

## Development Setup
### Installation
To set up your environment and start developing check this [guide](https://gitlab.com/mutt_data/soam/-/blob/master/documentation/source/developers_starting_point.md).
### Pre-Commit for Version Control Integration

We use [pre-commit](https://pre-commit.com) to run several code scans and hooks like linters and formatters, defined in `.pre-commit-config.yaml`, on each staged file  that make the development cycle easier.

To install pre-commit hooks run
```bash
pre-commit install
pre-commit install -t push
```

## Style guide
`soam` follows [PEP8](https://www.python.org/dev/peps/pep-0008/).

If you installed the [pre-commit hooks](#pre-commit) you shouldn't worry too much about style, since they will fix it for you or warn you about styling errors. We use the following hooks:

- [black](https://github.com/psf/black): an opinionated code formatting tool that ensures consistency across all projects using it.
- [flake8](https://github.com/PyCQA/flake8): a tool to enforce style guide.
- [mypy](https://github.com/python/mypy): a static type checker for Python.
- [pylint](https://github.com/PyCQA/pylint): a source code, bug and quality checker.
- [isort](https://github.com/timothycrosley/isort): a utility to sort imports alphabetically, and automatically separated into sections and by type.

## Docstrings
We use either [numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) or [google style](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings) docstring formatting. It's usually good to include the following docstrings:
- Module level docstring giving a general overview of what it does.
  - It may include TODOs
  - It may include examples
- Class dosctrings explaining what it is
- Method/functions to explain what it does and what it's parameters are

## Testing
`soam` uses the [pytest framework](https://docs.pytest.org/en/latest/) to test `soam`.

To run the default test suite run this:
```bash
pytest
```

Note that some tests may depend on external dependencies not installed with `[dev]` if you want to run the full set of tests use `[all]` instead, running this:
```bash
pip install -e .[all]
```

Run coverage:
```bash
pytest --cov-report html:cov_html --tb=short -q --cov-report term-missing --cov=. tests/
```
That should output a short summary and generate a dir `cov_html/` with a detailed HTML report that can be viewed by opening `index.html` in your browser.

To run the tests with [nox](https://nox.thea.codes/en/stable/):
```bash
nox --session tests
```

### Regression testing
[Regression testing](https://en.wikipedia.org/wiki/Regression_testing) to ensure new changes have not broken previously working features.

## Documentation
`soam` uses [Sphinx](https://www.sphinx-doc.org/en/master/) to autogenerate it's [docs](https://mutt_data.gitlab.io/soam/) that are automatically built from [docstrings](#docstrings) and pushed by the [CI jobs](#cicd-jobs). Check the [style guide](#style-guide) section for notes on docstrings. Pushing all the docs is too cumbersome. You can generate them locally by doing:

```bash
pip install .[all]
cd docs
make html
```

And open `docs/build/html/index.html` on your browser of choice.

Alternatively you can see the docs for the `master` branch [here.](https://mutt_data.gitlab.io/soam/index.html)

## Versioning
`soam` uses [SemVer](https://semver.org). To keep things easy, we've included [bump2version](https://github.com/c4urself/bump2version/) as a dev dependency. You can use `bump2version minor` to increase the minor number.

Please remember to bump the version when submitting your PR!

## Deprecation

Before fully deprecating a feature or making a breaking change, give users a `DeprecationWarning` and enough time for them to migrate their code.

### Decorator

`soam` uses [deprecated](https://github.com/tantale/deprecated) decorators to implement `DeprecationWarning`.

Add a `DeprecationWarning` considering indicate:
- How to achieve similar behavior if an alternative is available or a reason for the deprecation if no clear alternative is available.
- The versions number when the functionality was deprecated and when the EOL will be.

To do this, decorate your deprecated function with **@deprecated** decorator:

```python
from deprecated import deprecated


@deprecated
def some_old_function(x, y):
    return x + y
```

You can also decorate a class or a method:

```python
from deprecated import deprecated


class SomeClass(object):
    @deprecated
    def some_old_method(self, x, y):
        return x + y


@deprecated
class SomeOldClass(object):
    pass
```

You can give a "reason" message to help the developer to choose another function/class:

```python
from deprecated import deprecated


@deprecated(reason="use another function")
def some_old_function(x, y):
    return x + y
```

### Release
Deprecation warning must be added in minor releases and EOL will be on the next major releases.

## PRs
Also called MRs (Merge Requests) in gitlab.

`soam` development follows a simple workflow:
- Assign yourself an issue
  - If there's none, [create it](#issues)
  - If you can't assign it yourself, ask someone to do it for you
- Create a new branch with a descriptive name
- Push to the remote
  - Open a [WIP](#WIP) PR to allow discussion and let others know where you're at with the issue
- Work on it 🤓
- When ready change the PR to [RFC](#RFC)
  - Make sure you run the pipelines once the PR leaves *Draft mode*, i.e on the [Merge Result.](https://docs.gitlab.com/ee/ci/merge_request_pipelines/pipelines_for_merged_results/).
- You'll need at least one approval to merge
  - Merge will be disabled if the [CI/CD pipelines are failing](#cicd-jobs)
  - If you can't merge it yourself, ask your last approver to merge it
  - Please squash the commits and delete the branch
- Congrats and thanks for your contribution 🎉

Please keep PRs minimal. Try to keep the modified files to the bare needed for the issue you are working on. This will make the PR's changes more readable and allow for a quicker interaction with reviewers.

### WIP
WIP stands for **W**ork **i**n **P**rogress. WIP PRs are not yet ready to be merged. They allow for:
- Other project members to know you are working on something
- Early feedback, e.g. if you are doing something wrong or they see a problem down the road with your approach

You can tag a PR as WIP using the `WIP:` prefix on you PR title.

### RFC
RFC stands for **R**equest **f**or **C**omments. It means you consider the issue is solved by the code in the PR and are asking people to review your changes.

### CI/CD jobs

All commits pushed to branches in pull requests will trigger CI jobs that install `soam` in a gitlab-provided docker-env and all the extras, run all tests and check for linting. Look at [.gitlab-ci.yml](.gitlab-ci.yml) for more details on this and as well as the official [docs](https://docs.gitlab.com/ce/ci/README.html). Note that only PRs that pass the CI will be allowed to merge.

`NOTE:` If your commit message contains [ci skip] or [skip ci], without capitalization, the job will be skipped i.e. no CI job will be spawned for that push.

Alternatively, one can pass the ci.skip Git push option if using Git 2.10 or newer: `git push -o ci.skip` more info in [here](https://docs.gitlab.com/ce/ci/yaml/README.html#skipping-builds).

`IMPORTANT:`. If you skip the CI job it will not disable the option to do the merge, be careful when doing this.

**Important note on coverage:** A regex that captures the output from `pytest-cov` has been set from Settings -> CI/CD -> General Pipelines -> Test coverage parsing

## Rules of Thumb
- Important changes should be mentioned in the [README.md](README.md)
- Documentation must be updated.
- Every change should be present in the [CHANGELOG.md](CHANGELOG.md)<!-- gfmd-start -->
![Mermaid diagram](https://kroki.io/mermaid/svg/eNoDAAAAAAE=)

<details>
<summary><sup><sub>Diagram source code</sub></sup></summary>

```mermaid

```
</details>
<!-- gfmd-end -->
 soam
Thanks for your interest in contributing to `soam` 🎉. These are the guidelines for contributions. Reading them will help you get started on how to make useful contributions.

## Foreword
This guide is not final. It will evolve over time, as we learn and add new voices to the project. Check it from time to time and feel free to make suggestions 😃

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Issues](#issues)
  - [Labels](#labels)
  - [Security issues](#security-issues)
- [Development Setup](#development-setup)
  - [Installation](#installation)
  - [Pre-Commit for Version Control Integration](#pre-commit-for-version-control-integration)
- [Style guide](#style-guide)
- [Docstrings](#docstrings)
- [Testing](#testing)
  - [Regression testing](#regression-testing)
- [Documentation](#documentation)
- [Versioning](#versioning)
- [Deprecation](#deprecation)
  - [Decorator](#decorator)
  - [Release](#release)
- [PRs](#prs)
  - [WIP](#wip)
  - [RFC](#rfc)
  - [CI/CD jobs](#cicd-jobs)
- [Rules of Thumb](#rules-of-thumb)

## Code of Conduct
One of our core values at Mutt is that **we are an open team**. We all make mistakes and need help fixing them. We foster psychological safety. We clearly express it when we don’t know something and ask for advice.

We expect everyone contributing to `soam` to follow this principle. Be kind, don't be rude, keep it friendly; learn, teach, ask and help.

## Issues

Before submitting an issue, first check on the [issues tracker](https://gitlab.com/mutt_data/soam/issues) if there is already one trying to cover that topic, to avoid duplicates. Otherwise we invite you to create it. And if you feel that your issue can be categorized you can use this labels:

### Labels

| name | description | shortcuts |
| ---------- | ----------- | ------ |
| `bug` | Report a bug | [Look](https://gitlab.com/mutt_data/soam/issues?scope=all&utf8=✓&state=opened&label_name[]=bug) for `bug` or [create](https://gitlab.com/mutt_data/soam/-/issues/new?issuable_template=Bug) one
|`feature-request`|Request for a new feature|[Look](https://gitlab.com/mutt_data/soam/issues?scope=all&utf8=✓&state=opened&label_name[]=feature-request) for `feature-request` or [create](https://gitlab.com/mutt_data/soam/-/issues/new?issuable_template=Feature) one
|`enhancement`|Propose an enhancement|[Look](https://gitlab.com/mutt_data/soam/issues?scope=all&utf8=✓&state=opened&label_name[]=enhancement) for `enhancement` or [create](https://gitlab.com/mutt_data/soam/-/issues/new?issuable_template=Enhancement) one
|`discussion`|Start a new discussion|[Look](https://gitlab.com/mutt_data/soam/issues?scope=all&utf8=✓&state=opened&label_name[]=discussion) for `discussion` or [create](https://gitlab.com/mutt_data/soam/-/issues/new?issuable_template=Discussion) one

### Security issues
If you find a security related bug or any kind of security rellated issue, **please DO NOT file a public issue**. Sensitive security-related issues should be reported to privately to the repo owner along with a PoC if possible. You can [send us an email](mailto:security@muttdata.ai) and we'll go from there.

## Development Setup
### Installation

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

Next steps:
* If you already have the project running the last step before making your first commit is to review the
[development pipeline](development_pipeline.md).
* If you want more information about the main classes or patterns in the project go to [classes document](classes.md).
* If you need to understand a library, technology or concept in the project you can check the
[references](references.md).

### Pre-Commit for Version Control Integration

We use [pre-commit](https://pre-commit.com) to run several code scans and hooks like linters and formatters, defined in `.pre-commit-config.yaml`, on each staged file  that make the development cycle easier.

To install pre-commit hooks run
```bash
pre-commit install
pre-commit install -t push
```

## Style guide
SoaM follows [PEP8](https://www.python.org/dev/peps/pep-0008/).

If you installed the [pre-commit hooks](#pre-commit) you shouldn't worry too much about style, since they will fix it for you or warn you about styling errors. We use the following hooks:

- [black](https://github.com/psf/black): an opinionated code formatting tool that ensures consistency across all projects using it.
- [flake8](https://github.com/PyCQA/flake8): a tool to enforce style guide.
- [mypy](https://github.com/python/mypy): a static type checker for Python.
- [pylint](https://github.com/PyCQA/pylint): a source code, bug and quality checker.
- [isort](https://github.com/timothycrosley/isort): a utility to sort imports alphabetically, and automatically separated into sections and by type.

## Docstrings
We use either [numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) or [google style](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings) docstring formatting. It's usually good to include the following docstrings:
- Module level docstring giving a general overview of what it does.
  - It may include TODOs
  - It may include examples
- Class dosctrings explaining what it is
- Method/functions to explain what it does and what it's parameters are

## Testing
SoaM uses the [pytest framework](https://docs.pytest.org/en/latest/) to test SoaM.

To run the default test suite run this:
```bash
pytest
```

Note that some tests may depend on external dependencies not installed with `[dev]` if you want to run the full set of tests use `[all]` instead, running this:
```bash
pip install -e .[all]
```

Run coverage:
```bash
pytest --cov-report html:cov_html --tb=short -q --cov-report term-missing --cov=. tests/
```
That should output a short summary and generate a dir `cov_html/` with a detailed HTML report that can be viewed by opening `index.html` in your browser.

To run the tests with [nox](https://nox.thea.codes/en/stable/):
```bash
nox --session tests
```

### Regression testing
[Regression testing](https://en.wikipedia.org/wiki/Regression_testing) to ensure new changes have not broken previously working features.

## Documentation
SoaM uses [Sphinx](https://www.sphinx-doc.org/en/master/) to autogenerate it's [docs](https://mutt_data.gitlab.io/soam/) that are automatically built from [docstrings](#docstrings) and pushed by the [CI jobs](#cicd-jobs). Check the [style guide](#style-guide) section for notes on docstrings. Pushing all the docs is too cumbersome. You can generate them locally by doing:

```bash
pip install .[all]
cd documentation
rm -r build
sphinx-apidoc -f -o source ../soam # To create the modules documentation
make html # To bundle the documentation
```

And open `docs/build/html/index.html` on your browser of choice.

Note that for simple tests that don't depend on external libraries you can install only the Sphinx deps.

This documentation is created during CI using [GitLab Pages](https://docs.gitlab.com/ee/user/project/pages/).

Alternatively you can see the docs for the `master` branch [here.](https://mutt_data.gitlab.io/soam/index.html)

We are using the following extensions:
 - [napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html) to
 create the rst files from the code documentation.
 - [autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) to
 include the code documentation that napoleon generates.
 - [m2r2](https://github.com/crossnox/m2r2) to easily include markdown files in the
 documentation.

## Versioning
SoaM uses [SemVer](https://semver.org). To keep things easy, we've included [bump2version](https://github.com/c4urself/bump2version/) as a dev dependency. You can use `bump2version minor` to increase the minor number.

Please remember to bump the version when submitting your PR!

## Deprecation

Before fully deprecating a feature or making a breaking change, give users a `DeprecationWarning` and enough time for them to migrate their code.

### Decorator

SoaM uses [deprecated](https://github.com/tantale/deprecated) decorators to implement `DeprecationWarning`.

Add a `DeprecationWarning` considering indicate:
- How to achieve similar behavior if an alternative is available or a reason for the deprecation if no clear alternative is available.
- The versions number when the functionality was deprecated and when the EOL will be.

To do this, decorate your deprecated function with **@deprecated** decorator:

```python
from deprecated import deprecated


@deprecated
def some_old_function(x, y):
    return x + y
```

You can also decorate a class or a method:

```python
from deprecated import deprecated


class SomeClass(object):
    @deprecated
    def some_old_method(self, x, y):
        return x + y


@deprecated
class SomeOldClass(object):
    pass
```

You can give a "reason" message to help the developer to choose another function/class:

```python
from deprecated import deprecated


@deprecated(reason="use another function")
def some_old_function(x, y):
    return x + y
```

### Release
Deprecation warning must be added in minor releases and EOL will be on the next major releases.

## PRs
Also called MRs (Merge Requests) in gitlab.

SoaM development follows a simple workflow:
- Assign yourself an issue
  - If there's none, [create it](#issues)
  - If you can't assign it yourself, ask someone to do it for you
- Create a new branch with a descriptive name
- Push to the remote
  - Open a [WIP](#WIP) PR to allow discussion and let others know where you're at with the issue
- Work on it 🤓
- When ready change the PR to [RFC](#RFC)
  - Make sure you run the pipelines once the PR leaves *Draft mode*, i.e on the [Merge Result.](https://docs.gitlab.com/ee/ci/merge_request_pipelines/pipelines_for_merged_results/).
- You'll need at least one approval to merge
  - Merge will be disabled if the [CI/CD pipelines are failing](#cicd-jobs)
  - If you can't merge it yourself, ask your last approver to merge it
  - Please squash the commits and delete the branch
- Congrats and thanks for your contribution 🎉

Please keep PRs minimal. Try to keep the modified files to the bare needed for the issue you are working on. This will make the PR's changes more readable and allow for a quicker interaction with reviewers.

### WIP
WIP stands for **W**ork **i**n **P**rogress. WIP PRs are not yet ready to be merged. They allow for:
- Other project members to know you are working on something
- Early feedback, e.g. if you are doing something wrong or they see a problem down the road with your approach

You can tag a PR as WIP using the `WIP:` prefix on you PR title.

### RFC
RFC stands for **R**equest **f**or **C**omments. It means you consider the issue is solved by the code in the PR and are asking people to review your changes.

### CI/CD jobs

All commits pushed to branches in pull requests will trigger CI jobs that install SoaM in a gitlab-provided docker-env and all the extras, run all tests and check for linting. Look at [.gitlab-ci.yml](.gitlab-ci.yml) for more details on this and as well as the official [docs](https://docs.gitlab.com/ce/ci/README.html). Note that only PRs that pass the CI will be allowed to merge.

`NOTE:` If your commit message contains [ci skip] or [skip ci], without capitalization, the job will be skipped i.e. no CI job will be spawned for that push.

Alternatively, one can pass the ci.skip Git push option if using Git 2.10 or newer: `git push -o ci.skip` more info in [here](https://docs.gitlab.com/ce/ci/yaml/README.html#skipping-builds).

`IMPORTANT:`. If you skip the CI job it will not disable the option to do the merge, be careful when doing this.

**Important note on coverage:** A regex that captures the output from `pytest-cov` has been set from Settings -> CI/CD -> General Pipelines -> Test coverage parsing

## Rules of Thumb
- Important changes should be mentioned in the [README.md](README.md)
- Documentation must be updated.
- Every change should be present in the [CHANGELOG.md](CHANGELOG.md)
