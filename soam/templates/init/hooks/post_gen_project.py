import shutil

from pkg_resources import resource_filename

package_name = "{{cookiecutter.package_name}}"
project_name = "{{cookiecutter.project_name}}"

PROJECT_NAME = "soam"
DB_MIGRATIONS = "db_migrations"

shutil.copytree(
    resource_filename(PROJECT_NAME, DB_MIGRATIONS), f"{project_name}/{DB_MIGRATIONS}",
)
