"""Plotting module for Delver."""
import logging
from datetime import timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

"""
from constants import (
    DAILY_TIME_GRANULARITY,
    DS_COL,
    HOURLY_TIME_GRANULARITY,
    NATION_NAME,
    PARENT_LOGGER,
    PLOT_CONFIG,
    TIME_GRANULARITY_NAME_MAP,
)
from forecaster import OUTLIER_SIGN_COL, Y_COL, YHAT_COL, YHAT_LOWER_COL, YHAT_UPPER_COL
"""
# CLI defaults
FORECASTER_FUTURE_WINDOW = 15
FORECASTER_FUTURE_WINDOW_CUMSUM_KPI = 30
FORECASTER_TRAIN_WINDOW = 90
ANOMALY_WINDOW = 7
CLF_TRAIN_WINDOW = 7
SAMPLE_SIZE = 2
TOP_K_INFLUENCERS = 12

DS_COL = "ds"
Y_COL = "y"
PRED_COLS = ["ds", "yhat", "yhat_lower", "yhat_upper", Y_COL]


# Time
HOURS = 24
END_HOUR = 23
HOURLY_TIME_GRANULARITY = "H"
DAILY_TIME_GRANULARITY = "D"

TIME_GRANULARITY_NAME_MAP = {
    HOURLY_TIME_GRANULARITY: "hourly",
    DAILY_TIME_GRANULARITY: "daily",
}
TIME_GRANULARITIES = list(TIME_GRANULARITY_NAME_MAP.keys())


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
        "title": "Anomalías en {kpi} - {geo_gran} Argentina {start_date:%d-%b} al {end_date:%d-%b}",
    }
}


FORECAST_DATE_COL = "forecast_date"
FLOOR_COL = "floor"
CAP_COL = "cap"
DAY_NAME = "day_name"
YHAT_LOWER_COL = "yhat_lower"
YHAT_UPPER_COL = "yhat_upper"
YHAT_COL = "yhat"
TREND_COL = "trend"
OUTLIER_VALUE_COL = "outlier_value"
OUTLIER_SIGN_COL = "outlier_sign"


pd.plotting.register_matplotlib_converters()

# logger = logging.getLogger(f'{PARENT_LOGGER}.{__name__}')


def _set_time_locator_interval(fig, ax, time_granularity, plot_conf):
    major_locator = getattr(mdates, "DayLocator")
    major_locator_interval = (
        plot_conf["daily_major_interval"]
        if time_granularity == DAILY_TIME_GRANULARITY
        else plot_conf["hourly_major_interval"]
    )
    date_format = "%Y-%b-%d"

    if time_granularity == HOURLY_TIME_GRANULARITY:
        date_format = "%b %a %d"
        minor_locator_interval = plot_conf["hourly_minor_locator_interval"]
        minor_date_format = "%H"
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=minor_locator_interval))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter(minor_date_format))

        plt.tick_params(
            axis="x", which="minor", labelsize=plot_conf["hourly_font_size"]
        )
        ax.xaxis.set_tick_params(
            which="minor", labelrotation=plot_conf["hourly_minor_labelrotation"]
        )

        ax.set_xticklabels(ax.get_xticklabels(), fontsize=plot_conf["hourly_font_size"])
        ax.xaxis.set_tick_params(which="major", pad=plot_conf["hourly_major_pad"])

    ax.xaxis.set_major_locator(major_locator(interval=major_locator_interval))
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))

    ax.xaxis_date()  # interpret the x-axis values as dates
    fig.autofmt_xdate()
    return fig, ax


def _base_10_tick_scaler(median_val):
    for i in reversed(range(1, 4)):
        if median_val / (10 ** i) >= 1:
            return i
    else:
        return 0


def _create_common_series(df, ds_col, sd, ed=None):  # pylint:disable=unused-argument
    """Get series data for start/end date range.

    Return filtered values and dates."""
    window = df.query(f"@sd <= {ds_col}")
    if ed:
        window = window.query(f"{ds_col} <= @ed")
    window_dates = window[ds_col].dt.to_pydatetime()
    return window, window_dates


def anomaly_plot(
    kpi_plot_name,
    kpi_name,
    granularity_val,
    forecast_df,
    end_date,
    anomaly_window,
    time_granularity=DAILY_TIME_GRANULARITY,
):
    """Plot trend, forecast and anomalies with history, anomaly and forecast phases."""
    # TODO: Break this function into smaller pieces

    time_name = TIME_GRANULARITY_NAME_MAP[time_granularity]
    PLOT_CONF = PLOT_CONFIG["anomaly_plot"]
    COLORS = PLOT_CONF["colors"]
    LABELS = PLOT_CONF["labels"]
    history_window = PLOT_CONF[f"{time_name}_history_window"]
    future_window = PLOT_CONF[f"{time_name}_future_window"]

    anomaly_sd = end_date - timedelta(days=(anomaly_window - 1))
    history_sd = anomaly_sd - timedelta(days=(history_window))
    future_date = end_date + timedelta(days=future_window)

    history, history_dates = _create_common_series(
        forecast_df, DS_COL, history_sd, anomaly_sd
    )
    # Note: we need to convert datetime values in series to pydatetime explicitly
    # See: https://stackoverflow.com/q/29329725/2149400
    anomaly_win, anomaly_win_dates = _create_common_series(
        forecast_df, DS_COL, anomaly_sd, end_date
    )
    forecast, forecast_dates = _create_common_series(
        forecast_df, DS_COL, end_date, future_date
    )

    # FIXME: For some reason sometimes we don't have data for the end date so the last
    # day in the anomaly window is -1 (or null)
    anomaly_win[Y_COL].replace(-1, np.nan, inplace=True)

    date_format = "%Y-%b-%d"
    fig_size = PLOT_CONF["daily_fig_size"]
    if time_granularity == HOURLY_TIME_GRANULARITY:
        date_format += " %Hhs"
        fig_size = PLOT_CONF["hourly_fig_size"]

    fig, ax = plt.subplots(figsize=fig_size)
    ax.plot(
        history_dates, history[Y_COL], color=COLORS["history"], label=LABELS["history"]
    )
    ax.fill_between(
        history_dates,
        history[YHAT_LOWER_COL],
        history[YHAT_UPPER_COL],
        color=COLORS["history_fill"],
        alpha=0.2,
    )
    ax.plot(
        anomaly_win_dates,
        anomaly_win[Y_COL],
        color=COLORS["anomaly_win"],
        label=LABELS["anomaly_win"].format(anomaly_window=anomaly_window),
    )
    ax.fill_between(
        anomaly_win_dates,
        anomaly_win[YHAT_LOWER_COL],
        anomaly_win[YHAT_UPPER_COL],
        color=COLORS["anomaly_win_fill"],
        alpha=0.6,
    )
    ax.plot(
        forecast_dates,
        forecast[YHAT_COL],
        ls="--",
        color=COLORS["forecast"],
        label=LABELS["forecast"],
    )
    ax.fill_between(
        forecast_dates,
        forecast[YHAT_LOWER_COL],
        forecast[YHAT_UPPER_COL],
        color=COLORS["forecast"],
        alpha=0.2,
    )

    for _, o in forecast_df.query(
        f"{DS_COL} >= @history_dates.min() & {OUTLIER_SIGN_COL} != 0"
    ).iterrows():
        o_ds = o[f"{DS_COL}"]
        color = COLORS["outliers_history"]
        o_label = ""
        if o_ds.to_pydatetime() in np.unique(anomaly_win_dates):
            color = (
                COLORS["outliers_positive"]
                if o[OUTLIER_SIGN_COL] > 0
                else COLORS["outliers_negative"]
            )
            o_label = LABELS["outlier"].format(date=f"{o_ds:{date_format}}")
        ax.plot_date(
            x=o_ds,
            y=o[Y_COL],
            marker="o",
            markersize=6,
            alpha=0.7,
            color=color,
            label=o_label,
        )

    ax.set_xlabel(LABELS["xlabel"])
    ax.set_xlim([history_dates.min(), forecast_dates.max()])
    fig, ax = _set_time_locator_interval(fig, ax, time_granularity, PLOT_CONF)

    base_10_scale = _base_10_tick_scaler(forecast_df[Y_COL].median())
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: f"{(y * (10 ** -base_10_scale)):g}")
    )
    base_10_scale_zeros = base_10_scale * "0"
    ax.set_ylabel(
        LABELS["ylabel"].format(
            kpi_plot_name=kpi_plot_name, base_10_scale_zeros=base_10_scale_zeros
        )
    )

    # s_geo_gran = '' if s_geo_gran == NATION_NAME.lower() else f'{s_geo_gran.title()} /'
    # title = PLOT_CONF['title'].format(
    #    kpi=kpi_name, geo_gran=s_geo_gran, start_date=anomaly_sd, end_date=end_date
    # )
    title = PLOT_CONF["title"].format(
        kpi=kpi_name,
        granularity_val=granularity_val,
        start_date=anomaly_sd,
        end_date=end_date,
    )
    # title =  kpi_name
    if time_granularity == HOURLY_TIME_GRANULARITY:
        title += f" {end_date:%H}hs"
    ax.set_title(title)
    ax.grid(True, which="major", c=COLORS["axis_grid"], ls="-", lw=1, alpha=0.2)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    plt.tight_layout()
    return fig


class ForecastPlotter:
    def __init__(self, factor_val, save_suffix="", save_path=None):
        self.factor_val = factor_val
        self.save_suffix = save_suffix
        self.save_path = save_path

    # def plot(self, forecaster, time_range_conf, target_col, kpi_plot_name, kpi_name):
    def plot(self, forecaster_df, time_range_conf, target_col, kpi_plot_name, kpi_name):
        fig = anomaly_plot(
            kpi_plot_name=kpi_plot_name,
            kpi_name=kpi_name,
            # s_geo_gran=self.factor_val,
            granularity_val=self.factor_val,
            # forecast_df=forecaster.forecast,
            forecast_df=forecast_df,
            end_date=time_range_conf.end_date,
            anomaly_window=time_range_conf.anomaly_window,
            time_granularity=time_range_conf.time_granularity,
        )
        fn = "_".join(
            [
                "forecast",
                f"{time_range_conf.start_date:%Y%m%d%H}",
                f"{time_range_conf.end_date:%Y%m%d%H}",
                target_col,
                self.save_suffix,
                ".png",
            ]
        )
        fn = self.save_path / fn
        logger.debug(f"Saving forecast figure to {fn}...")
        fig.savefig(fn, bbox_inches="tight")
        print(fn)
        plt.close()
