from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from soam.constants import (
    ANOMALY_PLOT,
    DS_COL,
    FIG_SIZE,
    MONTHLY_TIME_GRANULARITY,
    PLOT_CONFIG,
    Y_COL,
    YHAT_COL,
)
from soam.forecast_plotter import ForecastPlotterTask


@pytest.fixture
def sample_data_df():
    # Taken from https://raw.githubusercontent.com/facebook/prophet/master/examples/example_retail_sales.csv
    return pd.DataFrame.from_records(
        np.array(
            [
                (253, '2013-02-01T00:00:00.000000000', 373938),
                (254, '2013-03-01T00:00:00.000000000', 421638),
                (255, '2013-04-01T00:00:00.000000000', 408381),
                (256, '2013-05-01T00:00:00.000000000', 436985),
                (257, '2013-06-01T00:00:00.000000000', 414701),
                (258, '2013-07-01T00:00:00.000000000', 422357),
                (259, '2013-08-01T00:00:00.000000000', 434950),
                (260, '2013-09-01T00:00:00.000000000', 396199),
                (261, '2013-10-01T00:00:00.000000000', 415740),
                (262, '2013-11-01T00:00:00.000000000', 423611),
                (263, '2013-12-01T00:00:00.000000000', 477205),
                (264, '2014-01-01T00:00:00.000000000', 383399),
                (265, '2014-02-01T00:00:00.000000000', 380315),
                (266, '2014-03-01T00:00:00.000000000', 432806),
                (267, '2014-04-01T00:00:00.000000000', 431415),
                (268, '2014-05-01T00:00:00.000000000', 458822),
                (269, '2014-06-01T00:00:00.000000000', 433152),
                (270, '2014-07-01T00:00:00.000000000', 443005),
                (271, '2014-08-01T00:00:00.000000000', 450913),
                (272, '2014-09-01T00:00:00.000000000', 420871),
                (273, '2014-10-01T00:00:00.000000000', 437702),
                (274, '2014-11-01T00:00:00.000000000', 437910),
                (275, '2014-12-01T00:00:00.000000000', 501232),
                (276, '2015-01-01T00:00:00.000000000', 397252),
                (277, '2015-02-01T00:00:00.000000000', 386935),
                (278, '2015-03-01T00:00:00.000000000', 444110),
                (279, '2015-04-01T00:00:00.000000000', 438217),
                (280, '2015-05-01T00:00:00.000000000', 462615),
                (281, '2015-06-01T00:00:00.000000000', 448229),
                (282, '2015-07-01T00:00:00.000000000', 457710),
                (283, '2015-08-01T00:00:00.000000000', 456340),
                (284, '2015-09-01T00:00:00.000000000', 430917),
                (285, '2015-10-01T00:00:00.000000000', 444959),
                (286, '2015-11-01T00:00:00.000000000', 444507),
                (287, '2015-12-01T00:00:00.000000000', 518253),
                (288, '2016-01-01T00:00:00.000000000', 400928),
                (289, '2016-02-01T00:00:00.000000000', 413554),
                (290, '2016-03-01T00:00:00.000000000', 460093),
                (291, '2016-04-01T00:00:00.000000000', 450935),
                (292, '2016-05-01T00:00:00.000000000', 471421),
            ],
            dtype=[('index', '<i8'), ('ds', '<M8[ns]'), ('y', '<i8')],
        )
    )


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
    tmp_path, sample_data_df
):  # pylint: disable=redefined-outer-name
    time_series = sample_data_df.iloc[:30]
    prediction = sample_data_df.iloc[30:]
    prediction = prediction.rename(columns={Y_COL: YHAT_COL})
    fpt = run_standard_ForecastPlotterTask(tmp_path, time_series, prediction)
    assert_out_paths_equal(['0_forecast_2013020100_2015080100_.png'], tmp_path)
    return fpt.fig


@pytest.mark.mpl_image_compare
def test_ForecastPlotterTask_overlapping(
    tmp_path, sample_data_df
):  # pylint: disable=redefined-outer-name
    time_series = sample_data_df
    prediction = sample_data_df.iloc[30:]
    prediction = prediction.rename(columns={Y_COL: YHAT_COL})
    prediction = perturb_ts(prediction, YHAT_COL, scale=0.1)
    fpt = run_standard_ForecastPlotterTask(tmp_path, time_series, prediction)
    assert_out_paths_equal(['0_forecast_2013020100_2015080100_.png'], tmp_path)
    return fpt.fig
