import nox


@nox.session(reuse_venv=True, python="3.7")
def tests(session):
    """Run all tests."""
    session.install(".")
    session.install(".[all]")

    cmd = ["pytest", "-v", "--mpl", "-n", "auto"]

    if session.posargs:
        cmd.extend(session.posargs)

    session.run(*cmd)

    session.run(
        "python",
        "-m",
        "pytest",
        "--nbval-lax",
        "notebook/examples/",
        "--current-env",
        "--no-cov",
    )


@nox.session(reuse_venv=True, python="3.7")
def lint(session):
    """Run all pre-commit hooks."""

    session.install(".")
    session.install(".[all]")
    session.run("pre-commit", "install")
    session.run("pre-commit", "run", "--show-diff-on-failure", "--all-files")


@nox.session(reuse_venv=True, python="3.7")
def bandit(session):
    """Run all pre-commit hooks."""
    session.install("bandit")

    session.run("bandit", "-r", "soam/", "-ll", "-c", "bandit.yaml")


@nox.session(reuse_venv=True, python="3.7")
def pyreverse(session):
    """Create class diagrams."""
    session.install(".")
    session.install(".[all]")
    session.install("pylint")

    # TODO: create smaller diagrams with portions of the project.
    session.run("pyreverse", "soam", "-o", "png", "--ignore", "pdf_report.py")

    session.run(
        "mv",
        "packages.png",
        "documentation/images/packages_dependencies.png",
        external=True,
    )
    session.run(
        "mv", "classes.png", "documentation/images/project_classes.png", external=True
    )
