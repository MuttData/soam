import nox


@nox.session(reuse_venv=True)
def tests(session):
    """Run all tests."""
    session.install(".")
    session.install(".[test]")

    cmd = ["pytest", "-n", "auto"]

    if session.posargs:
        cmd.extend(session.posargs)

    session.run(*cmd)


@nox.session(reuse_venv=True)
def lint(session):
    """Run all pre-commit hooks."""

    session.install(".")
    session.install(".[dev]")
    session.install(".[test]")

    session.run("pre-commit", "install")
    session.run("pre-commit", "run", "--show-diff-on-failure", "--all-files")


@nox.session(reuse_venv=True)
def bandit(session):
    """Run all pre-commit hooks."""
    session.install("bandit")

    session.run("bandit", "-r", "soam/", "-ll", "-c", "bandit.yaml")


@nox.session(reuse_venv=True)
def pyreverse(session):
    """Create class diagrams."""
    session.install("pylint")

    # TODO: create smaller diagrams with portions of the project.
    session.run("pyreverse", "soam", "-o", "png")

    session.run(
        "mv",
        "packages.png",
        "documentation/images/packages_dependencies.png",
        external=True,
    )
    session.run(
        "mv", "classes.png", "documentation/images/project_classes.png", external=True
    )