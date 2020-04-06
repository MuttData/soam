"""Constants and configurations setup for Delver project."""
from datetime import datetime, timedelta

# from sql_clauses import (  # NOQA:F401
#     GEO_GRAN_TO_COL_NAME_MAP,
#     MOVIMIENTOS_PP_GEO_GRAN_TO_CLAUSE_MAP,
# )

# CLI defaults
FORECASTER_FUTURE_WINDOW = 15
FORECASTER_FUTURE_WINDOW_CUMSUM_KPI = 30
FORECASTER_TRAIN_WINDOW = 90
ANOMALY_WINDOW = 7
CLF_TRAIN_WINDOW = 7
SAMPLE_SIZE = 2
TOP_K_INFLUENCERS = 12

# Global
PROJECT_NAME = "TFG Anomaly Detector"
ENV_DEV = "dev"
ENV_STG = "stg"
ENV_PRD = "prd"
POSSIBLE_ENVS = [ENV_DEV, ENV_STG, ENV_PRD]
DS_COL = "ds"
Y_COL = "y"
PRED_COLS = ["ds", "yhat", "yhat_lower", "yhat_upper", Y_COL]
SEED = 42
# GEO_GRANULARITIES = list(GEO_GRAN_TO_COL_NAME_MAP.keys())
# ALL_GEO_GRAN_COLS = list(GEO_GRAN_TO_COL_NAME_MAP.values())
# MOVI_PP_GEO_GRAN_COLS = list(
#     (GEO_GRAN_TO_COL_NAME_MAP[k] for k in MOVIMIENTOS_PP_GEO_GRAN_TO_CLAUSE_MAP)
# )

# Status
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"

# Time and Geo Granularity
HOURS = 24
END_HOUR = 23
HOURLY_TIME_GRANULARITY = "H"
DAILY_TIME_GRANULARITY = "D"

TIME_GRANULARITY_NAME_MAP = {
    HOURLY_TIME_GRANULARITY: "hourly",
    DAILY_TIME_GRANULARITY: "daily",
}
TIME_GRANULARITIES = list(TIME_GRANULARITY_NAME_MAP.keys())

# Factor levels constants
MAX_FACTOR_LEVELS = 25
MIN_FACTOR_LEVEL_DATAPOINTS = 10

REGRESSOR_PREFIX = "regr_"
# VALUE based on historical 2018 histogram of commercial ratio triplica offers
# TRIPLICA_OFFER_THRESHOLD_VALUE = 100

# TIME values
YESTERDAY = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

# SQL consts
# [REMOVED]

# Maps dimensions to corresponding sql filenames
# [REMOVED]


# Rating Groups
# [REMOVED]


# Copa Libertadores
# [REMOVED]

# Influencers Drill Down
# [REMOVED]

# Mail report constants
MAIL_WORST_FACTOR_VALS_NR = 3

DEFAULT_PROPHET_ARGS = dict(
    # changepoint_range=0.75,
    # yearly_seasonality=False,
    # changepoint_prior_scale=0.04,
    # daily_seasonality=30,
    # weekly_seasonality=20,
    # holidays_prior_scale=10,
    interval_width=0.8
    #            seasonality_prior_scale=5,
)

# Aggregated mail report constants
AGGREGATED_MAIL_IMAGES = ["aggregated_summary"]

# Plots config
PLOT_CONFIG = {
    "anomaly_plot": {
        "daily_fig_size": (10, 6),
        "hourly_fig_size": (13, 9),
        "colors": {
            "history": "k",
            "history_fill": "gray",
            "anomaly_win": "dodgerblue",
            "anomaly_win_fill": "lightskyblue",
            "forecast": "darkviolet",
            "outliers_history": "black",
            "outliers_positive": "green",
            "outliers_negative": "red",
            "axis_grid": "gray",
        },
        "daily_major_interval": 3,
        "daily_future_window": 15,  # Number of future days posterior to anomaly-win
        "daily_history_window": 30,  # Number of history days prior to anomaly-win
        "hourly_major_interval": 2,
        "hourly_history_window": 14,
        "hourly_future_window": 5,
        "hourly_font_size": 7,
        "hourly_minor_labelrotation": 40,
        "hourly_major_pad": 25,
        "hourly_minor_locator_interval": 8,
        "labels": {
            "xlabel": "Fechas",
            "ylabel": "{kpi_plot_name} ({base_10_scale_zeros}s)",
            "history": "Historia",
            "anomaly_win": "Últimos {anomaly_window} días",
            "forecast": "Pronóstico",
            "outlier": "Outlier: {date}",
        },
        # 'title': 'Anomalías en {kpi} - {geo_gran} Argentina {start_date:%d-%b} al {end_date:%d-%b}',
        "title": "Anomalías en {kpi} - {granularity_val} {start_date:%d-%b} al {end_date:%d-%b}",
    }
}

# Logger config
PARENT_LOGGER = "SOAM"
