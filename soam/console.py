# console.py
"""
Console
----------
Console commands and utilities.
"""
import click
from cookiecutter.main import cookiecutter
from pkg_resources import resource_filename

from soam.cfg import INIT_TEMPLATE_DIR


@click.group()
def cli():
    pass


@cli.command()
@click.option('--output', help='Output directory', default='.')
def init(output):
    """Create a sample project structure ready to use SoaM"""
    cookiecutter(
        resource_filename(__name__, INIT_TEMPLATE_DIR), output_dir=output,
    )
