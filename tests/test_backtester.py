from copy import deepcopy
import unittest

from darts.models import ExponentialSmoothing, Theta
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

from soam.backtester import Backetester, compute_metrics
from soam.constants import (
    ANOMALY_PLOT,
    DS_COL,
    FIG_SIZE,
    MONTHLY_TIME_GRANULARITY,
    PLOT_CONFIG,
    Y_COL,
)
from soam.forecast_plotter import ForecastPlotterTask
from soam.forecaster import Forecaster
from soam.helpers import BaseDataFrameTransformer
from soam.transformer import Transformer
from tests.helpers import sample_data_df  # pylint: disable=unused-import


def test_compute_metrics():
    metrics = {
        "mae": mean_absolute_error,
        "mse": mean_squared_error,
    }
    y_true = [3, -0.5, 2, 7]
    y_pred = [2.5, 0.0, 2, 8]
    expected_output = {'mae': 0.5, 'mse': 0.375}
    output = compute_metrics(y_true, y_pred, metrics)
    unittest.TestCase().assertDictEqual(expected_output, output)


class SimpleProcessor(BaseDataFrameTransformer):
    def __init__(self, **fit_params):
        self.preproc = StandardScaler(**fit_params)

    def fit(self, df_X):
        self.preproc.fit(df_X[Y_COL].values.reshape(-1, 1))
        return self

    def transform(self, df_X, inplace=True):
        if not inplace:
            df_X = df_X.copy()
        df_X[Y_COL] = self.preproc.transform(df_X[Y_COL].values.reshape(-1, 1)) + 10
        return df_X


def assert_backtest_fold_result(rv, ranges=None, metrics=None, plots=None):
    assert tuple(rv) == ('ranges', 'metrics', 'plot')
    assert rv['ranges'] == ranges
    assert rv['plot'].name == plots
    unittest.TestCase().assertDictEqual(rv['metrics'], metrics)


def assert_backtest_all_folds_result(rvs, expected_values):
    assert len(rvs) == len(expected_values)
    for rv, evs in zip(rvs, expected_values):
        assert_backtest_fold_result(rv, **evs)


def test_integration_Backtester_single_fold(
    tmp_path, sample_data_df
):  # pylint: disable=redefined-outer-name
    train_data = sample_data_df
    forecaster = Forecaster(model=Theta(), output_length=10)
    preprocessor = Transformer(SimpleProcessor())
    plot_config = deepcopy(PLOT_CONFIG)
    plot_config[ANOMALY_PLOT][MONTHLY_TIME_GRANULARITY][FIG_SIZE] = (8, 3)
    forecast_plotter = ForecastPlotterTask(
        path=tmp_path,
        metric_name='test',
        time_granularity=MONTHLY_TIME_GRANULARITY,
        plot_config=plot_config,
    )
    metrics = {
        "mae": mean_absolute_error,
        "mse": mean_squared_error,
    }

    backtester = Backetester(
        forecaster=forecaster,
        preprocessor=preprocessor,
        forecast_plotter=forecast_plotter,
        test_window=10,
        train_window=30,
        metrics=metrics,
    )
    rvs = backtester.run(train_data)

    expected_values = [
        {
            'ranges': (
                pd.Timestamp('2013-02-01 00:00:00'),
                pd.Timestamp('2015-07-01 00:00:00'),
                pd.Timestamp('2016-05-01 00:00:00'),
            ),
            'metrics': {'mae': 0.7878291094308457, 'mse': 1.3658751092701222},
            'plots': '0_forecast_2013020100_2015080100_.png',
        },
    ]
    assert_backtest_all_folds_result(rvs, expected_values)


def test_integration_Backtester_multi_fold(
    tmp_path, sample_data_df
):  # pylint: disable=redefined-outer-name
    train_data = pd.concat([sample_data_df] * 3)
    train_data[DS_COL] = pd.date_range(
        train_data[DS_COL].min(), periods=len(train_data), freq='MS'
    )
    model = ExponentialSmoothing()
    forecaster = Forecaster(model=model, output_length=10)
    preprocessor = Transformer(SimpleProcessor())
    plot_config = deepcopy(PLOT_CONFIG)
    plot_config[ANOMALY_PLOT][MONTHLY_TIME_GRANULARITY][FIG_SIZE] = (8, 3)
    forecast_plotter = ForecastPlotterTask(
        path=tmp_path,
        metric_name='test',
        time_granularity=MONTHLY_TIME_GRANULARITY,
        plot_config=plot_config,
    )
    metrics = {
        "mae": mean_absolute_error,
        "mse": mean_squared_error,
    }

    backtester = Backetester(
        forecaster=forecaster,
        preprocessor=preprocessor,
        forecast_plotter=forecast_plotter,
        test_window=30,
        train_window=30,
        metrics=metrics,
    )
    rvs = backtester.run(train_data)

    expected_values = [
        {
            'ranges': (
                pd.Timestamp('2013-02-01 00:00:00'),
                pd.Timestamp('2015-07-01 00:00:00'),
                pd.Timestamp('2018-01-01 00:00:00'),
            ),
            'metrics': {'mae': 1.2302525646461073, 'mse': 2.8245357205721384},
            'plots': '0_forecast_2013020100_2015080100_.png',
        },
        {
            'ranges': (
                pd.Timestamp('2015-08-01 00:00:00'),
                pd.Timestamp('2018-01-01 00:00:00'),
                pd.Timestamp('2020-07-01 00:00:00'),
            ),
            'metrics': {'mae': 0.8261577849244794, 'mse': 0.9293777664085056},
            'plots': '0_forecast_2015080100_2018020100_.png',
        },
        {
            'ranges': (
                pd.Timestamp('2018-02-01 00:00:00'),
                pd.Timestamp('2020-07-01 00:00:00'),
                pd.Timestamp('2023-01-01 00:00:00'),
            ),
            'metrics': {'mae': 1.1802703142819078, 'mse': 1.993944686736428},
            'plots': '0_forecast_2018020100_2020080100_.png',
        },
    ]
    assert_backtest_all_folds_result(rvs, expected_values)
