"""Forecast plotter tests."""
from copy import deepcopy
import locale

import numpy as np
import pytest

from soam.constants import (
    ANOMALY_PLOT,
    FIG_SIZE,
    MONTHLY_TIME_GRANULARITY,
    PLOT_CONFIG,
    Y_COL,
    YHAT_COL,
)
from soam.plotting.forecast_plotter import ForecastPlotterTask
from tests.helpers import sample_data_df  # pylint: disable=unused-import


@pytest.fixture
def set_time_locale():
    locale.setlocale(locale.LC_TIME, (None, None))


def perturb_ts(df, col, scale=1):
    """Add noise to ts
    """
    mean = df[col].mean() * scale
    df[col] += np.random.default_rng(42).uniform(
        low=-mean / 2, high=mean / 2, size=len(df)
    )
    return df


def assert_out_paths_equal(fnames, tmp_path):
    expected_out_files = [(tmp_path / fn).as_posix() for fn in fnames]
    out_files = [p.as_posix() for p in tmp_path.iterdir()]
    assert len(expected_out_files) == len(out_files)
    assert all(a == b for a, b in zip(expected_out_files, out_files))


def run_standard_ForecastPlotterTask(tmp_path, time_series, prediction):
    plot_config = deepcopy(PLOT_CONFIG)
    plot_config[ANOMALY_PLOT][MONTHLY_TIME_GRANULARITY][FIG_SIZE] = (8, 3)
    fpt = ForecastPlotterTask(
        path=tmp_path,
        metric_name='test',
        time_granularity=MONTHLY_TIME_GRANULARITY,
        plot_config=plot_config,
    )
    fpt.run(time_series, prediction)
    return fpt


@pytest.mark.mpl_image_compare
def test_ForecastPlotterTask_simple(
    tmp_path, sample_data_df, set_time_locale
):  # pylint: disable=redefined-outer-name,unused-argument
    time_series = sample_data_df.iloc[:30]
    prediction = sample_data_df.iloc[30:]
    prediction = prediction.rename(columns={Y_COL: YHAT_COL})
    fpt = run_standard_ForecastPlotterTask(tmp_path, time_series, prediction)
    assert_out_paths_equal(['0_forecast_2013020100_2015080100_.png'], tmp_path)
    return fpt.fig


@pytest.mark.mpl_image_compare
def test_ForecastPlotterTask_overlapping(
    tmp_path, sample_data_df, set_time_locale
):  # pylint: disable=redefined-outer-name,unused-argument
    time_series = sample_data_df
    prediction = sample_data_df.iloc[30:]
    prediction = prediction.rename(columns={Y_COL: YHAT_COL})
    prediction = perturb_ts(prediction, YHAT_COL, scale=0.1)
    fpt = run_standard_ForecastPlotterTask(tmp_path, time_series, prediction)
    assert_out_paths_equal(['0_forecast_2013020100_2015080100_.png'], tmp_path)
    return fpt.fig
