# constants.py
"""
Constants
----------
Constants for the whole project.
"""
from datetime import datetime, timedelta
import re

# Global
PROJECT_NAME = "SoaM"
DS_COL = "ds"
Y_COL = "y"
YHAT_COL = "yhat"
YHAT_LOWER_COL = "yhat_lower"
YHAT_UPPER_COL = "yhat_upper"

PRED_COLS = [DS_COL, YHAT_COL, YHAT_LOWER_COL, YHAT_UPPER_COL, Y_COL]
SEED = 42

FORECAST_DATE = "forecast_date"

SEED = 42

OUTLIER_SIGN_COL = "sign"

# Status
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"

# Time and Geo Granularity
HOURS = 24
END_HOUR = 23
HOURLY_TIME_GRANULARITY = "H"
DAILY_TIME_GRANULARITY = "D"
MONTHLY_TIME_GRANULARITY = "M"

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

# Aggregated mail report constants
AGGREGATED_MAIL_IMAGES = ["aggregated_summary"]

# Plot common config keys

HISTORY = "history"
FORECAST = "forecast"
OUTLIER = "outlier"
COLORS = "colors"
ANOMALY_PLOT = "anomaly_plot"
LABELS = "labels"
TITLE = "title"
ANOMALY_WIN = "anomaly_win"
ANOMALY_WIN_FILL = "anomaly_win_fill"
HISTORY_FILL = "history_fill"
OUTLIERS_HISTORY = "outliers_history"
OUTLIERS_POSITIVE = "outliers_positive"
OUTLIERS_NEGATIVE = "outliers_negative"
AXIS_GRID = "axis_grid"


# Daily and Hourly config
FIG_SIZE = "fig_size"
MAJOR_INTERVAL = "major_interval"
MINOR_INTERVAL = "minor_locator_interval"
FUTURE_WINDOW = "future_window"
HISTORY_WINDOW = "history_window"
FONT_SIZE = "font_size"
MINOR_LABEL_ROTATION = "minor_labelrotation"
MAJOR_PAD = "major_pad"
DATE_FORMAT = "date_format"

# Plots config
PLOT_CONFIG = {
    ANOMALY_PLOT: {
        HOURLY_TIME_GRANULARITY: {
            FIG_SIZE: (13, 9),
            MAJOR_INTERVAL: 2,
            FUTURE_WINDOW: 5,
            HISTORY_WINDOW: 14,
            FONT_SIZE: 7,
            MINOR_LABEL_ROTATION: 40,
            MAJOR_PAD: 25,
            MINOR_INTERVAL: 8,
            DATE_FORMAT: "%Y-%b-%d %Hhs",
        },
        DAILY_TIME_GRANULARITY: {
            FIG_SIZE: (10, 6),
            MAJOR_INTERVAL: 3,
            FUTURE_WINDOW: 15,
            HISTORY_WINDOW: 60,
            FONT_SIZE: 7,
            DATE_FORMAT: "%Y-%b-%d",
        },
        MONTHLY_TIME_GRANULARITY: {
            FIG_SIZE: (13, 9),
            MAJOR_INTERVAL: 2,
            FUTURE_WINDOW: 5,
            HISTORY_WINDOW: 14,
            FONT_SIZE: 7,
            MINOR_LABEL_ROTATION: 40,
            MAJOR_PAD: 25,
            MINOR_INTERVAL: 8,
            DATE_FORMAT: "%Y-%b",
        },
        COLORS: {
            HISTORY: "orange",
            HISTORY_FILL: "gray",
            ANOMALY_WIN: "dodgerblue",
            ANOMALY_WIN_FILL: "lightskyblue",
            FORECAST: "blue",
            OUTLIERS_HISTORY: "black",
            OUTLIERS_POSITIVE: "green",
            OUTLIERS_NEGATIVE: "red",
            AXIS_GRID: "gray",
        },
        LABELS: {
            "xlabel": "Date",
            "ylabel": "{metric_name} ({base_10_scale_zeros}s)",
            HISTORY: "History",
            ANOMALY_WIN: "Last {anomaly_window} days",
            FORECAST: "Forecast",
            OUTLIER: "Outlier: {date}",
        },
        "title": "{plot_type} for {metric_name} {start_date:%d-%b} to {end_date:%d-%b}",
    }
}

# Saver Config
FLOW_FILE_NAME = "flow_tasks.csv"
LOCK_NAME = "flow.lock"

# Timeseries Extractor
DONT_AGGREGATE_SYMBOL = "#"
NEGATE_SYMBOL = "!"
PREFIX_SYMBOLS = DONT_AGGREGATE_SYMBOL + NEGATE_SYMBOL  # dims prefix symbols
regex_prefix_symbols = re.compile(f"^[{PREFIX_SYMBOLS }]*")
TIMESTAMP_COL = 'timestamp'
