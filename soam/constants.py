# constants.py
from datetime import datetime, timedelta

# CLI defaults
FORECASTER_FUTURE_WINDOW = 15
FORECASTER_FUTURE_WINDOW_CUMSUM_KPI = 30
FORECASTER_TRAIN_WINDOW = 90
ANOMALY_WINDOW = 7
CLF_TRAIN_WINDOW = 7
SAMPLE_SIZE = 2
TOP_K_INFLUENCERS = 12

# Global
PROJECT_NAME = "SoaM Anomaly Detector"
ENV_DEV = "dev"
ENV_STG = "stg"
ENV_PRD = "prd"
POSSIBLE_ENVS = [ENV_DEV, ENV_STG, ENV_PRD]
DS_COL = "ds"
Y_COL = "y"
PRED_COLS = ["ds", "yhat", "yhat_lower", "yhat_upper", Y_COL]
SEED = 42

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


# TIME values
YESTERDAY = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")


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
        "daily_fig_size": (15, 7),
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
        "daily_history_window": 60,  # Number of history days prior to anomaly-win
        "daily_minor_locator_interval": 1,
        "hourly_major_interval": 2,
        "hourly_history_window": 14,
        "hourly_future_window": 5,
        "hourly_font_size": 7,
        "hourly_minor_labelrotation": 40,
        "hourly_major_pad": 25,
        "hourly_minor_locator_interval": 8,
        "labels": {
            "xlabel": "Date",
            "ylabel": "{kpi_plot_name} ({base_10_scale_zeros}s)",
            "history": "History",
            "anomaly_win": "Last {anomaly_window} days",
            "forecast": "Forecast",
            "outlier": "Outlier: {date}",
        },
        "title": "[TEST] Anomalies for {kpi} - {granularity_val} {start_date:%d-%b} to {end_date:%d-%b}",
    }
}

# Logger config
PARENT_LOGGER = PROJECT_NAME
