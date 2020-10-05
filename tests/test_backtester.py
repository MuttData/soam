from copy import deepcopy
import unittest

from darts.models import Theta
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

from soam.backtester import Backetester, compute_metrics
from soam.constants import (
    ANOMALY_PLOT,
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
    assert len(rvs) == 1
    for rv in rvs:
        assert tuple(rv) == ('ranges', 'metrics', 'plot')
        assert rv['ranges'] == (
            pd.Timestamp('2013-02-01 00:00:00'),
            pd.Timestamp('2015-07-01 00:00:00'),
            pd.Timestamp('2015-07-01 00:00:00'),
        )
        assert rv['plot'].name == '0_forecast_2013020100_2015080100_.png'
        unittest.TestCase().assertDictEqual(
            rv['metrics'], {'mae': 0.7878291094308457, 'mse': 1.3658751092701222},
        )
