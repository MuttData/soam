import nox


@nox.session(reuse_venv=True, python=["3.7", "3.8"])
def tests(session):
    """Run all tests."""
    session.install("pip==20.3.1")

    session.install(".", "--use-deprecated=legacy-resolver")
    session.install(".[test]", "--use-deprecated=legacy-resolver")

    cmd = ["pytest", "-v", "--mpl", "-n", "auto"]

    if session.posargs:
        cmd.extend(session.posargs)

    session.run(*cmd)


@nox.session(reuse_venv=True, python=["3.7", "3.8"])
def lint(session):
    """Run all pre-commit hooks."""
    session.install("pip==20.3.1")
    session.install(".", "--use-deprecated=legacy-resolver")
    session.install(".[dev]", "--use-deprecated=legacy-resolver")
    session.install(".[test]", "--use-deprecated=legacy-resolver")
    session.install(".[slack]", "--use-deprecated=legacy-resolver")

    session.run("pre-commit", "install")
    session.run("pre-commit", "run", "--show-diff-on-failure", "--all-files")


@nox.session(reuse_venv=True, python=["3.7", "3.8"])
def bandit(session):
    """Run all pre-commit hooks."""
    session.install("pip==20.3.1")
    session.install("bandit", "--use-deprecated=legacy-resolver")

    session.run("bandit", "-r", "soam/", "-ll", "-c", "bandit.yaml")


@nox.session(reuse_venv=True, python=["3.7", "3.8"])
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
