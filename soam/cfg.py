
from pathlib import Path

from pkg_resources import resource_string

from soam.utils import make_dirs, template

KPI_TABLE_BASENAME = "kpis"
SOAM_RUN_TABLE_BASENAME = "soam_runs"
SOAM_RUN_FACTOR_CONF_TABLE_BASENAME = "soam_run_factor_conf"
FORECASTER_RUNS_TABLE_BASENAME = "forecaster_runs"
FORECASTER_VALUES_TABLE_BASENAME = "forecaster_values"
INFLUENCER_RUNS_TABLE_BASENAME = "influencer_runs"
INFLUENCER_VALUES_TABLE_BASENAME = "influencer_values"
DRILL_DOWN_RUNS_TABLE_BASENAME = "drill_down_runs"
DRILL_DOWN_VALUES_TABLE_BASENAME = "drill_down_values"
COSERIES_RUNS_TABLE_BASENAME = "coseries_runs"
COSERIES_DIMENSIONS_TABLE_BASENAME = "coseries_dimensions"
COSERIES_VALUES_TABLE_BASENAME = "coseries_values"
COSERIES_SCORES_TABLE_BASENAME = "coseries_scores"
TIMELINE_TABLE_BASENAME = "timeline"

# Setup paths
_project_dir = Path(__file__).resolve().parent
_p = Path("/tmp/anomalies/")
SQL_DIR = make_dirs(Path(_p, "resources"))
LOG_DIR = make_dirs(Path(_p, "tmp", "logs"))
DATA_DIR = make_dirs(Path(_p, "tmp", "data"))
DATA_DIR_TABULAR = make_dirs(Path(_p, "tmp", "data", "tabular"))
FIG_DIR = make_dirs(Path(_p, "tmp", "figures"))
RES_DIR = make_dirs(Path(_p, "tmp", "results"))

#SQL_TEMPLATE = utils.template(
#    str((_p / "resources" / "templates.sql").resolve())
#).module

# Table name setup
table_name_preffix = ""

# if ENV is not None:
#     table_name_preffix = f"{ENV}_"
table_name_preffix = ""

KPI_TABLE = f"{table_name_preffix}{KPI_TABLE_BASENAME}"
SOAM_RUN_TABLE = f"{table_name_preffix}{SOAM_RUN_TABLE_BASENAME}"
SOAM_RUN_FACTOR_CONF_TABLE = (
    f"{table_name_preffix}{SOAM_RUN_FACTOR_CONF_TABLE_BASENAME}"
)
FORECASTER_RUNS_TABLE = f"{table_name_preffix}{FORECASTER_RUNS_TABLE_BASENAME}"
FORECASTER_VALUES_TABLE = f"{table_name_preffix}{FORECASTER_VALUES_TABLE_BASENAME}"
INFLUENCER_RUNS_TABLE = f"{table_name_preffix}{INFLUENCER_RUNS_TABLE_BASENAME}"
INFLUENCER_VALUES_TABLE = f"{table_name_preffix}{INFLUENCER_VALUES_TABLE_BASENAME}"
DRILL_DOWN_RUNS_TABLE = f"{table_name_preffix}{DRILL_DOWN_RUNS_TABLE_BASENAME}"
DRILL_DOWN_VALUES_TABLE = f"{table_name_preffix}{DRILL_DOWN_VALUES_TABLE_BASENAME}"
COSERIES_RUNS_TABLE = f"{table_name_preffix}{COSERIES_RUNS_TABLE_BASENAME}"
COSERIES_DIMENSIONS_TABLE = f"{table_name_preffix}{COSERIES_DIMENSIONS_TABLE_BASENAME}"
COSERIES_VALUES_TABLE = f"{table_name_preffix}{COSERIES_VALUES_TABLE_BASENAME}"
COSERIES_SCORES_TABLE = f"{table_name_preffix}{COSERIES_SCORES_TABLE_BASENAME}"
TIMELINE_TABLE = f"{table_name_preffix}{TIMELINE_TABLE_BASENAME}"

# Mail report
MAIL_TEMPLATE = template(
    resource_string(__name__, 'resources/mail_report.html').decode('utf-8')
).module
