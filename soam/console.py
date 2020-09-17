# console.py
"""
Console
----------
Console commands and utilities. It uses click library to run the app in a
command line interface.
It has a hook inside setup.py:
"entry_points={'console_scripts': ['soam = soam.console:cli']}"
"""
# from sys import argv
from typing import NoReturn

import click
from cookiecutter.main import cookiecutter
from pkg_resources import resource_filename

from soam.cfg import INIT_TEMPLATE_DIR


@click.group()
def cli() -> NoReturn:
    """
    TODO: review why we are using this.
    https://click.palletsprojects.com/en/7.x/commands/#callback-invocation
    """


@cli.command()
@click.option('--output', help='Output directory', default='.')
def init(output: str) -> str:
    """Create a sample project structure ready to use SoaM

    To create the sample project it will prompt the user for the following
     configurations: package_display_name, project_name, package_name,
     author_name, description.

    Parameters
    ----------
    output : str
        The path to make the scaffolding.

    Returns
    -------
    dict
        Returns the root of the sample project: "output/package_name".
    """
    return cookiecutter(
        resource_filename(__name__, INIT_TEMPLATE_DIR), output_dir=output,
    )


# TODO: include __main__ for debugging purposes
# if __name__ == "__main__":
#     assert len(argv) == 2
#     dd = init(['--output', argv[1]])
