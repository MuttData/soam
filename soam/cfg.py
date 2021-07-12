# cfg.py
"""
Configurations
----------
Configuration values for the SlackReport, MailReport, DBSaver and Mlflow.
"""
from pathlib import Path
import tempfile
from typing import Optional

from decouple import AutoConfig
from muttlib.utils import get_default_jinja_template, make_dirs
from pkg_resources import resource_string

SQLITE = "sqlite"

SOAM_RUN_TABLE_BASENAME = "soam_flow_runs"
SOAM_RUN_FACTOR_CONF_TABLE_BASENAME = "soam_flow_run_factor_conf"
SOAM_TASK_RUNS_TABLE_BASENAME = "tasks_runs"
FORECASTER_VALUES_TABLE_BASENAME = "forecaster_values"
EXTRACT_VALUES_TABLE_BASENAME = "extract_values"

# Setup paths
# _p = Path("/tmp/soam/")
_p = tempfile.mkdtemp()
SQL_DIR = make_dirs(Path(_p, "resources"))
LOG_DIR = make_dirs(Path(_p, "tmp", "logs"))
DATA_DIR = make_dirs(Path(_p, "tmp", "data"))
DATA_DIR_TABULAR = make_dirs(Path(_p, "tmp", "data", "tabular"))
FIG_DIR = make_dirs(Path(_p, "tmp", "figures"))
RES_DIR = make_dirs(Path(_p, "tmp", "results"))

# Report paths and configs
MAIL_REPORT = "resources/mail_report.html"

# Template paths
TEMPLATE_DIR = "templates"
INIT_TEMPLATE = "init"
INIT_TEMPLATE_DIR = f"{TEMPLATE_DIR}/{INIT_TEMPLATE}"
TEMPLATES = [INIT_TEMPLATE]

# Text config
UTF_ENCODING = "utf-8"

# Table name setup
table_name_preffix = ""

SOAM_FLOW_RUN_TABLE = f"{table_name_preffix}{SOAM_RUN_TABLE_BASENAME}"
SOAM_FLOW_RUN_TABLE_FACTOR_CONF_TABLE = (
    f"{table_name_preffix}{SOAM_RUN_FACTOR_CONF_TABLE_BASENAME}"
)
SOAM_TASK_RUNS_TABLE = f"{table_name_preffix}{SOAM_TASK_RUNS_TABLE_BASENAME}"
FORECASTER_VALUES_TABLE = f"{table_name_preffix}{FORECASTER_VALUES_TABLE_BASENAME}"
# TODO: replace syntax to be length compliant
# FORECASTER_VALUES_TABLE = (f"{table_name_preffix}"
#                            f"{FORECASTER_VALUES_TABLE_BASENAME}")
EXTRACT_VALUES_TABLE = f"{table_name_preffix}{EXTRACT_VALUES_TABLE_BASENAME}"


# Mail report
MAIL_TEMPLATE = get_default_jinja_template(
    resource_string(__name__, MAIL_REPORT).decode(UTF_ENCODING)
).module

# Mlflow tracking config
# Set to True if tracking is on
TRACKING_IS_ACTIVE = False
# Local file paths should be prefixed with "file:/", default is ./mlruns
# http URIs and Databricks workspaces can be used too.
TRACKING_URI = ''


def get_db_cred(setting_path: Optional[str] = None) -> dict:
    """Read the setting.ini file and retrieve the database credentials

    Parameters
    ----------
    setting_path : str, optional
        The path for the .ini document with the settings.

    Returns
    -------
    dict
        A dict containing: username, dialect, password, database, port, host.
    """
    config = AutoConfig(search_path=setting_path)
    db_cred = {}

    db_cred["username"] = config("DB_USER")
    db_cred["dialect"] = config("DB_DIALECT")
    db_cred["password"] = config("DB_PASSWORD")
    db_cred["database"] = config("DB_NAME")
    db_cred["port"] = config("DB_PORT")
    db_cred["host"] = config("DB_IP")

    return db_cred


def get_slack_cred(setting_path: Optional[str] = None) -> dict:
    """Retrieve the Slack credentials

    Parameters
    ----------
    setting_path : str, optional
        The path for the .ini document with the settings.

    Returns
    -------
    dict
        A dict containing the slack token.
    """
    config = AutoConfig(search_path=setting_path)
    slack_creds = {}

    slack_creds["token"] = config("SLACK_TOKEN")

    return slack_creds


def get_smtp_cred(setting_path: Optional[str] = None) -> dict:
    """Retrieve the SMTP credentials

    Parameters
    ----------
    setting_path : str, optional
        The path for the .ini document with the settings.

    Returns
    -------
    dict
        A dict containing: user_address, password, mail_from, host, port.
    """
    config = AutoConfig(search_path=setting_path)
    smtp_creds = {}

    smtp_creds["user_address"] = config("SMTP_USER")
    smtp_creds["password"] = config("SMTP_PASS")
    smtp_creds["mail_from"] = config("SMTP_FROM")
    smtp_creds["host"] = config("SMTP_HOST")
    smtp_creds["port"] = config("SMTP_PORT")

    return smtp_creds


def get_db_uri(setting_path: Optional[str]) -> str:
    """Retrieve the uri for the database.

    Parameters
    ----------
    setting_path : str, optional
        The path for the .ini document with the settings.

    Returns
    -------
    str
        A string with the database uri.
    """
    db_cred = get_db_cred(setting_path)

    if db_cred["dialect"] == SQLITE:
        return f"{db_cred['dialect']}:///{db_cred['database']}"

    return f"{db_cred['dialect']}://{db_cred['username']}:{db_cred['password']}@{db_cred['host']}:{db_cred['port']}/{db_cred['database']}"
    # TODO: replace syntax to be length compliant
    # return (f"{db_cred['dialect']}://{db_cred['username']}:"
    #         f"db_cred['password']}@{db_cred['host']}:"
    #         f"{db_cred['port']}/{db_cred['database']}")
