"""Backtester"""
from copy import deepcopy
import unittest

import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

from soam.constants import (
    ANOMALY_PLOT,
    DS_COL,
    FIG_SIZE,
    MONTHLY_TIME_GRANULARITY,
    PLOT_CONFIG,
    Y_COL,
)
from soam.models.prophet import SkProphet
from soam.plotting import ForecastPlotterTask
from soam.workflow import (
    Backtester,
    BaseDataFrameTransformer,
    Forecaster,
    Transformer,
    compute_metrics,
)
from soam.workflow.backtester import METRICS_KEYWORD, PLOT_KEYWORD, RANGES_KEYWORD
from tests.helpers import sample_data_df  # pylint: disable=unused-import


def test_compute_metrics():
    """Function to compute performance metrics."""
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
    """Create a Simple Processor object."""

    def __init__(self, **fit_params):  # pylint:disable=super-init-not-called
        self.preproc = StandardScaler(**fit_params)

    def fit(self, df_X):
        self.preproc.fit(df_X[Y_COL].values.reshape(-1, 1))
        return self

    def transform(self, df_X, inplace=True):
        if not inplace:
            df_X = df_X.copy()
        df_X[Y_COL] = self.preproc.transform(df_X[Y_COL].values.reshape(-1, 1)) + 10
        return df_X


def assert_backtest_fold_result_common_checks(rv, ranges=None, plots=None):
    """Backtest fold result common checks assertion."""
    assert tuple(rv) == (RANGES_KEYWORD, METRICS_KEYWORD, PLOT_KEYWORD)
    assert rv[RANGES_KEYWORD] == ranges
    assert rv[PLOT_KEYWORD].name == plots


def assert_backtest_fold_result(rv, ranges=None, metrics=None, plots=None):
    """Backtest fold result assertion."""
    assert_backtest_fold_result_common_checks(rv, ranges=ranges, plots=plots)
    for metric_name, values in metrics.items():
        assert metric_name in rv[METRICS_KEYWORD]
        if isinstance(values, dict):
            for measure_name, value in values.items():
                assert value, pytest.approx(rv[METRICS_KEYWORD][measure_name], 0.01)
        else:
            assert values, pytest.approx(rv[METRICS_KEYWORD][metric_name], 0.01)


def assert_backtest_all_folds_result(rvs, expected_values):
    """Backtest all fold result assertion."""
    assert len(rvs) == len(expected_values)
    for rv, evs in zip(rvs, expected_values):
        assert_backtest_fold_result(rv, **evs)


def assert_backtest_fold_result_aggregated(rv, ranges=None, metrics=None, plots=None):
    """Backtest fold result aggregated assertion."""
    assert_backtest_fold_result_common_checks(rv, ranges=ranges, plots=plots)
    output_metrics = pd.DataFrame(rv[METRICS_KEYWORD])
    expected_metrics = pd.DataFrame(metrics)
    pd.testing.assert_frame_equal(output_metrics, expected_metrics, rtol=1e-1)


def assert_backtest_all_folds_result_aggregated(rvs, expected_values):
    """Backtest all fold result aggregated assertion."""
    assert len(rvs) == len(expected_values)
    for rv, evs in zip(rvs, expected_values):
        assert_backtest_fold_result_aggregated(rv, **evs)


def test_integration_backtester_single_fold(
    tmp_path, sample_data_df
):  # pylint: disable=redefined-outer-name
    """Backtest single fold integration test."""
    test_window = 10
    train_data = sample_data_df
    forecaster = Forecaster(model=SkProphet(), output_length=test_window)
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

    backtester = Backtester(
        forecaster=forecaster,
        preprocessor=preprocessor,
        forecast_plotter=forecast_plotter,
        test_window=test_window,
        train_window=30,
        metrics=metrics,
    )
    rvs = backtester.run(train_data)
    expected_values = [
        {
            RANGES_KEYWORD: (
                pd.Timestamp('2013-02-01 00:00:00'),
                pd.Timestamp('2015-07-01 00:00:00'),
                pd.Timestamp('2016-05-01 00:00:00'),
            ),
            METRICS_KEYWORD: {'mae': 0.19286372252777645, 'mse': 0.07077117049346579},
            'plots': '0_forecast_2013020100_2015080100_.png',
        },
    ]
    assert_backtest_all_folds_result(rvs, expected_values)


def test_integration_backtester_multi_fold(
    tmp_path, sample_data_df  # pylint: disable=redefined-outer-name
):
    """Backtest multi fold integration test."""
    test_window = 30
    train_data = pd.concat([sample_data_df] * 3)
    train_data[DS_COL] = pd.date_range(
        train_data[DS_COL].min(), periods=len(train_data), freq='MS'
    )
    model = SkProphet()
    forecaster = Forecaster(model=model, output_length=test_window)
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

    backtester = Backtester(
        forecaster=forecaster,
        preprocessor=preprocessor,
        forecast_plotter=forecast_plotter,
        test_window=test_window,
        train_window=30,
        metrics=metrics,
    )
    rvs = backtester.run(train_data)
    expected_values = [
        {
            RANGES_KEYWORD: (
                pd.Timestamp('2013-02-01 00:00:00'),
                pd.Timestamp('2015-07-01 00:00:00'),
                pd.Timestamp('2018-01-01 00:00:00'),
            ),
            METRICS_KEYWORD: {'mae': 1.140921182444867, 'mse': 2.4605768804352675},
            'plots': '0_forecast_2013020100_2015080100_.png',
        },
        {
            RANGES_KEYWORD: (
                pd.Timestamp('2015-08-01 00:00:00'),
                pd.Timestamp('2018-01-01 00:00:00'),
                pd.Timestamp('2020-07-01 00:00:00'),
            ),
            METRICS_KEYWORD: {'mae': 1.600049020613293, 'mse': 4.383723067139095},
            'plots': '0_forecast_2015080100_2018020100_.png',
        },
        {
            RANGES_KEYWORD: (
                pd.Timestamp('2018-02-01 00:00:00'),
                pd.Timestamp('2020-07-01 00:00:00'),
                pd.Timestamp('2023-01-01 00:00:00'),
            ),
            METRICS_KEYWORD: {'mae': 3.1358162976127217, 'mse': 12.666965373730687},
            'plots': '0_forecast_2018020100_2020080100_.png',
        },
    ]
    assert_backtest_all_folds_result(rvs, expected_values)


# TODO: It maybe a good visual aggregation to include all metrics in one plot. This
# TODO: is not possible with the current implementation.
def test_integration_backtester_multi_fold_default_aggregation(
    tmp_path, sample_data_df  # pylint: disable=redefined-outer-name
):
    """Backtest multi fold default aggregation integration test."""
    test_window = 30
    train_data = pd.concat([sample_data_df] * 3)
    train_data[DS_COL] = pd.date_range(
        train_data[DS_COL].min(), periods=len(train_data), freq='MS'
    )
    model = SkProphet()
    forecaster = Forecaster(model=model, output_length=test_window)
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

    backtester = Backtester(
        forecaster=forecaster,
        preprocessor=preprocessor,
        forecast_plotter=forecast_plotter,
        test_window=test_window,
        train_window=30,
        metrics=metrics,
        aggregation="default",
    )
    rvs = backtester.run(train_data)
    expected_values = [
        {
            RANGES_KEYWORD: (
                pd.Timestamp('2013-02-01 00:00:00'),
                pd.Timestamp('2023-01-01 00:00:00'),
            ),
            METRICS_KEYWORD: {
                'mae': {
                    'avg': 2.0269522786354313,
                    'max': 3.135813436023453,
                    'min': 1.344995687583762,
                },
                'mse': {
                    'avg': 6.761216280050696,
                    'max': 12.666927167728852,
                    'min': 3.233004063171241,
                },
            },
            'plots': '0_forecast_2018020100_2020080100_.png',
        }
    ]
    assert_backtest_all_folds_result_aggregated(rvs, expected_values)


def test_integration_backtester_multi_fold_custom_aggregations(
    tmp_path, sample_data_df  # pylint: disable=redefined-outer-name
):
    """Backtest multi fold custom aggregation integration test."""
    test_window = 30
    train_data = pd.concat([sample_data_df] * 3)
    train_data[DS_COL] = pd.date_range(
        train_data[DS_COL].min(), periods=len(train_data), freq='MS'
    )
    model = SkProphet()
    forecaster = Forecaster(model=model, output_length=test_window)
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
    aggregation = {
        METRICS_KEYWORD: {
            "weighted_begining": lambda metrics_list: (
                sum(
                    [
                        3 * val if idx == 0 else val
                        for idx, val in enumerate(metrics_list)
                    ]
                )
                / (len(metrics_list) + 2)
            ),
            "weighted_ending": lambda metrics_list: (
                sum(
                    [
                        3 * val if idx == len(metrics_list) - 1 else val
                        for idx, val in enumerate(metrics_list)
                    ]
                )
                / (len(metrics_list) + 2)
            ),
        },
        PLOT_KEYWORD: 1,
    }

    backtester = Backtester(
        forecaster=forecaster,
        preprocessor=preprocessor,
        forecast_plotter=forecast_plotter,
        test_window=test_window,
        train_window=30,
        metrics=metrics,
        aggregation=aggregation,
    )
    rvs = backtester.run(train_data)

    expected_values = [
        {
            RANGES_KEYWORD: (
                pd.Timestamp('2013-02-01 00:00:00'),
                pd.Timestamp('2023-01-01 00:00:00'),
            ),
            METRICS_KEYWORD: {
                'mae': {
                    'weighted_begining': 1.631725773112123,
                    'weighted_ending': 2.4296838191792647,
                },
                'mse': {
                    'weighted_begining': 4.886483816435117,
                    'weighted_ending': 8.969039213753284,
                },
            },
            'plots': '0_forecast_2015080100_2018020100_.png',
        }
    ]
    assert_backtest_all_folds_result_aggregated(rvs, expected_values)


def test_integration_backtester_multi_fold_custom_metric_aggregation_default_plot(
    tmp_path, sample_data_df  # pylint: disable=redefined-outer-name
):
    """Backtest multi fold custom metric aggregation default plot integration test."""
    test_window = 30
    train_data = pd.concat([sample_data_df] * 3)
    train_data[DS_COL] = pd.date_range(
        train_data[DS_COL].min(), periods=len(train_data), freq='MS'
    )
    model = SkProphet()
    forecaster = Forecaster(model=model, output_length=test_window)
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
    aggregation = {
        METRICS_KEYWORD: {
            "weighted_begining": lambda metrics_list: (
                sum(
                    [
                        3 * val if idx == 0 else val
                        for idx, val in enumerate(metrics_list)
                    ]
                )
                / (len(metrics_list) + 2)
            ),
            "weighted_ending": lambda metrics_list: (
                sum(
                    [
                        3 * val if idx == len(metrics_list) - 1 else val
                        for idx, val in enumerate(metrics_list)
                    ]
                )
                / (len(metrics_list) + 2)
            ),
        }
    }

    backtester = Backtester(
        forecaster=forecaster,
        preprocessor=preprocessor,
        forecast_plotter=forecast_plotter,
        test_window=test_window,
        train_window=30,
        metrics=metrics,
        aggregation=aggregation,
    )
    rvs = backtester.run(train_data)

    expected_values = [
        {
            RANGES_KEYWORD: (
                pd.Timestamp('2013-02-01 00:00:00'),
                pd.Timestamp('2023-01-01 00:00:00'),
            ),
            METRICS_KEYWORD: {
                'mae': {
                    'weighted_begining': 1.631725773112123,
                    'weighted_ending': 2.4296838191792647,
                },
                'mse': {
                    'weighted_begining': 4.886483816435117,
                    'weighted_ending': 8.969039213753284,
                },
            },
            'plots': '0_forecast_2018020100_2020080100_.png',
        }
    ]
    assert_backtest_all_folds_result_aggregated(rvs, expected_values)


def test_integration_backtester_multi_fold_custom_plot_aggregation_default_metric(
    tmp_path, sample_data_df  # pylint: disable=redefined-outer-name
):
    """Backtest multi fold default metric aggregation custom plot integration test."""
    test_window = 30
    train_data = pd.concat([sample_data_df] * 3)
    train_data[DS_COL] = pd.date_range(
        train_data[DS_COL].min(), periods=len(train_data), freq='MS'
    )
    model = SkProphet()
    forecaster = Forecaster(model=model, output_length=test_window)
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
    aggregation = {
        PLOT_KEYWORD: 1,
    }

    backtester = Backtester(
        forecaster=forecaster,
        preprocessor=preprocessor,
        forecast_plotter=forecast_plotter,
        test_window=test_window,
        train_window=30,
        metrics=metrics,
        aggregation=aggregation,
    )
    rvs = backtester.run(train_data)

    expected_values = [
        {
            RANGES_KEYWORD: (
                pd.Timestamp('2013-02-01 00:00:00'),
                pd.Timestamp('2023-01-01 00:00:00'),
            ),
            METRICS_KEYWORD: {
                'mae': {
                    'avg': 2.0269522786354313,
                    'max': 3.135813436023453,
                    'min': 1.344995687583762,
                },
                'mse': {
                    'avg': 6.761216280050696,
                    'max': 12.666927167728852,
                    'min': 3.233004063171241,
                },
            },
            'plots': '0_forecast_2015080100_2018020100_.png',
        }
    ]
    assert_backtest_all_folds_result_aggregated(rvs, expected_values)
