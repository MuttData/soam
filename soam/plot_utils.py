# plot_utils.py
"""
Plot Utils
----------
Auxiliary functions for the Forecast Plotter.

See Also
--------
forecast_plotter.py.ForecastPlotter : Postprocessor to plot the forecasts.
"""
import logging
from datetime import timedelta
from typing import Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from soam.constants import (
    ANOMALY_WIN,
    ANOMALY_WIN_FILL,
    COLORS,
    DAILY_TIME_GRANULARITY,
    DATE_FORMAT,
    DS_COL,
    FIG_SIZE,
    FONT_SIZE,
    FORECAST,
    HISTORY,
    HISTORY_FILL,
    HOURLY_TIME_GRANULARITY,
    LABELS,
    MAJOR_INTERVAL,
    MAJOR_PAD,
    MINOR_INTERVAL,
    MINOR_LABEL_ROTATION,
    MONTHLY_TIME_GRANULARITY,
    OUTLIER_SIGN_COL,
    OUTLIERS_HISTORY,
    OUTLIERS_NEGATIVE,
    OUTLIERS_POSITIVE,
    PARENT_LOGGER,
    PLOT_CONFIG,
    Y_COL,
    YHAT_COL,
    YHAT_LOWER_COL,
    YHAT_UPPER_COL,
)

DAYLOCATOR = "DayLocator"

pd.plotting.register_matplotlib_converters()

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


def _set_time_locator_interval(fig: Figure, ax: Axes, time_granularity: str,
                               plot_conf: dict) -> Tuple[Figure, Axes]:
    major_locator = getattr(mdates, DAYLOCATOR)
    major_locator_interval = plot_conf[MAJOR_INTERVAL]
    date_format = "%Y-%b-%d"

    if time_granularity == MONTHLY_TIME_GRANULARITY:
        date_format = "%Y-%b"

    if time_granularity == HOURLY_TIME_GRANULARITY:
        date_format = "%b %a %d"
        minor_locator_interval = plot_conf[MINOR_INTERVAL]
        minor_date_format = "%H"
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=minor_locator_interval))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter(minor_date_format))

        plt.tick_params(axis="x", which="minor", labelsize=plot_conf[FONT_SIZE])
        ax.xaxis.set_tick_params(
            which="minor", labelrotation=plot_conf[MINOR_LABEL_ROTATION]
        )

        ax.set_xticklabels(ax.get_xticklabels(), fontsize=plot_conf[FONT_SIZE])
        ax.xaxis.set_tick_params(which="major", pad=plot_conf[MAJOR_PAD])

    ax.xaxis.set_major_locator(major_locator(interval=major_locator_interval))
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))

    ax.xaxis_date()  # interpret the x-axis values as dates
    fig.autofmt_xdate()
    return fig, ax


def _base_10_tick_scaler(median_val: float) -> int:
    for i in reversed(range(1, 4)):
        if median_val / (10 ** i) >= 1:
            return i
    else:
        return 0


def _create_common_series(df: pd.DataFrame, ds_col: str, sd,
                          ed=None) -> Tuple[pd.DataFrame, np.ndarray]:  # pylint:disable=unused-argument
    """Get series data for start/end date range.

    Return filtered values and dates."""
    window = df.query(f"@sd <= {ds_col}")
    if ed:
        window = window.query(f"{ds_col} <= @ed")
    window_dates = window[ds_col].dt.to_pydatetime()
    return window, window_dates


def create_forecast_figure(df: pd.DataFrame, metric_name: str, end_date,
                           forecast_window, anomaly_window: int = 0,
                           time_granularity:
                           str = DAILY_TIME_GRANULARITY) -> Figure:
    """Plot trend, forecast and anomalies with history, anomaly and forecast phases."""

    PLOT_CONF = PLOT_CONFIG["anomaly_plot"]
    PLOT_TIME_CONF = PLOT_CONF[time_granularity]
    COLOR_CONF = PLOT_CONF[COLORS]
    LABEL_CONF = PLOT_CONF[LABELS]
    future_window = forecast_window
    history_window = len(df) - forecast_window

    anomaly_sd = end_date - timedelta(days=(anomaly_window))
    history_sd = anomaly_sd - timedelta(days=(history_window))
    future_date = end_date + timedelta(days=future_window)

    # Note: we need to convert datetime values in series to pydatetime explicitly
    # See: https://stackoverflow.com/q/29329725/2149400
    history, history_dates = _create_common_series(df, DS_COL, history_sd, anomaly_sd)
    anomaly_win, anomaly_win_dates = _create_common_series(
        df, DS_COL, anomaly_sd, end_date
    )
    forecast, forecast_dates = _create_common_series(df, DS_COL, end_date, future_date)

    date_format = PLOT_TIME_CONF[DATE_FORMAT]
    fig_size = PLOT_TIME_CONF[FIG_SIZE]

    fig, ax = plt.subplots(figsize=fig_size)
    ax.plot(
        history_dates,
        history[Y_COL],
        color=COLOR_CONF[HISTORY],
        label=LABEL_CONF[HISTORY],
    )
    ax.plot(
        forecast_dates,
        forecast[YHAT_COL],
        ls="--",
        color=COLOR_CONF[FORECAST],
        label=LABEL_CONF[FORECAST],
    )

    if YHAT_LOWER_COL in df and YHAT_UPPER_COL in df:
        ax.plot(
            anomaly_win_dates,
            anomaly_win[Y_COL],
            color=COLOR_CONF[ANOMALY_WIN],
            label=LABEL_CONF[ANOMALY_WIN].format(anomaly_window=anomaly_window),
        )
        ax.fill_between(
            history_dates,
            history[YHAT_LOWER_COL],
            history[YHAT_UPPER_COL],
            color=COLOR_CONF[HISTORY_FILL],
            alpha=0.2,
        )

        ax.fill_between(
            anomaly_win_dates,
            anomaly_win[YHAT_LOWER_COL],
            anomaly_win[YHAT_UPPER_COL],
            color=COLOR_CONF[ANOMALY_WIN_FILL],
            alpha=0.6,
        )

        ax.fill_between(
            forecast_dates,
            forecast[YHAT_LOWER_COL],
            forecast[YHAT_UPPER_COL],
            color=COLOR_CONF[FORECAST],
            alpha=0.2,
        )

        for _, o in df.query(
            f"{DS_COL} >= @history_dates.min() & {OUTLIER_SIGN_COL} != 0"
        ).iterrows():
            o_ds = o[f"{DS_COL}"]
            color = COLOR_CONF[OUTLIERS_HISTORY]
            o_label = ""
            if o_ds.to_pydatetime() in np.unique(anomaly_win_dates):
                color = (
                    COLOR_CONF[OUTLIERS_POSITIVE]
                    if o[OUTLIER_SIGN_COL] > 0
                    else COLOR_CONF[OUTLIERS_NEGATIVE]
                )
                o_label = LABEL_CONF["outlier"].format(date=f"{o_ds:{date_format}}")
            ax.plot_date(
                x=o_ds,
                y=o[Y_COL],
                marker="o",
                markersize=6,
                alpha=0.7,
                color=color,
                label=o_label,
            )

    ax.set_xlabel(LABEL_CONF["xlabel"])
    ax.set_xlim([history_dates.min(), forecast_dates.max()])
    fig, ax = _set_time_locator_interval(fig, ax, time_granularity, PLOT_TIME_CONF)

    base_10_scale = _base_10_tick_scaler(df[Y_COL].median())
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: f"{(y * (10 ** -base_10_scale)):g}")
    )
    base_10_scale_zeros = base_10_scale * "0"
    ax.set_ylabel(
        LABEL_CONF["ylabel"].format(
            metric_name=metric_name, base_10_scale_zeros=base_10_scale_zeros
        )
    )

    if anomaly_window > 0:
        plot_type = "Anomaly"
        start_date = anomaly_sd
    else:
        plot_type = "Forecast"
        start_date = end_date + timedelta(days=1)
        end_date = future_date
    title = PLOT_CONF["title"].format(
        plot_type=plot_type,
        metric_name=metric_name,
        start_date=start_date,
        end_date=end_date,
    )

    if time_granularity == HOURLY_TIME_GRANULARITY:
        title += f" {end_date:%H}hs"
    ax.set_title(title)
    ax.grid(True, which="major", c=COLOR_CONF["axis_grid"], ls="-", lw=1, alpha=0.2)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    plt.tight_layout()
    return fig
