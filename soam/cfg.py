from pathlib import Path

from decouple import AutoConfig, config
from muttlib.utils import make_dirs, template
from pkg_resources import resource_string

SOAM_RUN_TABLE_BASENAME = "soam_runs"
SOAM_RUN_FACTOR_CONF_TABLE_BASENAME = "soam_run_factor_conf"
FORECASTER_RUNS_TABLE_BASENAME = "forecaster_runs"
FORECASTER_VALUES_TABLE_BASENAME = "forecaster_values"

# Setup paths
_p = Path("/tmp/soam/")
SQL_DIR = make_dirs(Path(_p, "resources"))
LOG_DIR = make_dirs(Path(_p, "tmp", "logs"))
DATA_DIR = make_dirs(Path(_p, "tmp", "data"))
DATA_DIR_TABULAR = make_dirs(Path(_p, "tmp", "data", "tabular"))
FIG_DIR = make_dirs(Path(_p, "tmp", "figures"))
RES_DIR = make_dirs(Path(_p, "tmp", "results"))

# Report paths and configs
MAIL_REPORT = "resources/mail_report.html"
UTF_ENCODING = "utf-8"

# Table name setup
table_name_preffix = ""

SOAM_RUN_TABLE = f"{table_name_preffix}{SOAM_RUN_TABLE_BASENAME}"
SOAM_RUN_FACTOR_CONF_TABLE = (
    f"{table_name_preffix}{SOAM_RUN_FACTOR_CONF_TABLE_BASENAME}"
)
FORECASTER_RUNS_TABLE = f"{table_name_preffix}{FORECASTER_RUNS_TABLE_BASENAME}"
FORECASTER_VALUES_TABLE = f"{table_name_preffix}{FORECASTER_VALUES_TABLE_BASENAME}"

# Mail report
MAIL_TEMPLATE = template(
    resource_string(__name__, MAIL_REPORT).decode(UTF_ENCODING)
).module


def get_db_cred(setting_path: str = "settings.ini") -> dict:
    """
    Read the setting.ini file and retrieve the database credentials
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


def get_slack_cred() -> dict:
    """
    Read the setting.ini file and retrieve the Slack credentials
    """
    slack_creds = {}

    slack_creds["token"] = config("SLACK_TOKEN")

    return slack_creds


def get_db_uri(setting_path: str) -> str:
    db_cred = get_db_cred(setting_path)

    return f"{db_cred['dialect']}://{db_cred['username']}:{db_cred['password']}@{db_cred['host']}:{db_cred['port']}/{db_cred['database']}"
