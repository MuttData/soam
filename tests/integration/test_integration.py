from copy import deepcopy

from darts.models import ExponentialSmoothing, Prophet
from darts.timeseries import TimeSeries
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error, mean_squared_error

from soam.constants import (
    ANOMALY_PLOT,
    DS_COL,
    FIG_SIZE,
    MONTHLY_TIME_GRANULARITY,
    PLOT_CONFIG,
    YHAT_COL,
)
from soam.core import SoamFlow
from soam.plotting import ForecastPlotterTask
from soam.reporting import SlackReportTask
from soam.reporting.slack_report import (
    DEFAULT_FAREWELL_MESSAGE,
    DEFAULT_GREETING_MESSAGE,
)
from soam.savers import CSVSaver
from soam.workflow import Backtester, Forecaster, Transformer
from soam.workflow.backtester import METRICS_KEYWORD, RANGES_KEYWORD
from tests.helpers import sample_data_df  # noqa pylint:disable=unused-import
from tests.workflow.test_backtester import (
    SimpleProcessor,
    assert_backtest_all_folds_result,
)

# pylint:disable=protected-access, redefined-outer-name


def create_slack_message(
    predictions,
    metric,
    farewell_message=DEFAULT_FAREWELL_MESSAGE,
    greeting_message=DEFAULT_GREETING_MESSAGE,
):
    greeting_message.format(metric_name=metric)

    summary_entries = []
    summary_entries.append(greeting_message)

    for _, row in predictions.iterrows():
        date = row[DS_COL].strftime('%Y-%b-%d')
        value = "{:.2f}".format(row[YHAT_COL])
        summary_entries.append(f"• *[{date}]* {value}\n")

    summary_entries.append(farewell_message)
    return "\n".join(summary_entries)


def create_settings_file(path, content):
    # Code to acquire resource, e.g.:
    setting_path = path / "settings.ini"
    with open(setting_path, "w+") as f:
        f.write(content)
    return setting_path


def assert_saved_data(path, prefix):
    """Assert savers worked as expected."""
    assert len(list(path.glob(f"{prefix}*"))) == 1


@pytest.fixture
def expected_predictions() -> pd.DataFrame:
    pred = {
        DS_COL: pd.date_range("2016-06-01", "2017-01-01", freq="M"),
        "yhat": [
            470271.76,
            463427.89,
            471309.20,
            452983.13,
            452273.99,
            467814.56,
            528948.24,
        ],
    }
    return pd.DataFrame(pred)


def test_integration_forecast(
    mocker, sample_data_df, expected_predictions, tmp_path  # noqa: F811
):
    """Test simple prediction workflow."""
    # TODO: Test adding saver to flow
    test_run_name = "test_integration_forecasting"
    saver_data = CSVSaver(tmp_path)
    my_model = Prophet(weekly_seasonality=True, daily_seasonality=False)
    mocker.patch.object(my_model, 'fit')
    my_model.fit.return_value = my_model
    mocker.patch.object(my_model, 'predict')
    my_model.predict.return_value = TimeSeries.from_dataframe(
        expected_predictions, time_col=DS_COL, value_cols="yhat"
    )
    forecaster = Forecaster(my_model, savers=[saver_data])
    with SoamFlow(name=test_run_name, saver=None) as f:  # noqa
        preds_model = forecaster(time_series=sample_data_df, output_length=7)

    fs = f.run()

    assert 3 == len(fs.result[preds_model]._result.value)
    assert expected_predictions.ds.equals(fs.result[preds_model]._result.value[0].ds)
    assert expected_predictions.yhat.values == pytest.approx(
        fs.result[preds_model]._result.value[0].yhat, 0.1
    )
    assert fs.is_successful()
    assert_saved_data(tmp_path, test_run_name)


def test_integration_backtest(
    tmp_path, sample_data_df  # noqa: F811
):  # pylint: disable=redefined-outer-name
    """Test backtest run."""
    # TODO: Add savers assertions once integrated with Backtest
    test_run_name = "test_integration_backtesting"
    train_data = pd.concat([sample_data_df] * 3)
    train_data[DS_COL] = pd.date_range(
        train_data[DS_COL].min(), periods=len(train_data), freq='MS'
    )
    model = ExponentialSmoothing()
    forecaster = Forecaster(model=model, output_length=10)
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
        preprocessor=Transformer(SimpleProcessor()),
        forecast_plotter=forecast_plotter,
        test_window=30,
        train_window=30,
        metrics=metrics,
        aggregation="default",
    )

    with SoamFlow(name=test_run_name, saver=None) as f:  # noqa
        backtest = backtester(train_data)

    fs = f.run()

    expected_values = [
        {
            RANGES_KEYWORD: (
                pd.Timestamp('2013-02-01 00:00:00'),
                pd.Timestamp('2023-01-01 00:00:00'),
            ),
            METRICS_KEYWORD: {
                'mae': {
                    'avg': 1.0788936351761558,
                    'max': 1.230244804563136,
                    'min': 0.8261656309767738,
                },
                'mse': {
                    'avg': 1.9159537714659203,
                    'max': 2.8245066880319296,
                    'min': 0.9294099396294029,
                },
            },
            'plots': '0_forecast_2018020100_2020080100_.png',
        }
    ]
    rvs = fs.result[backtest]._result.value
    assert_backtest_all_folds_result(rvs, expected_values)


def test_integration_forecast_and_report(
    mocker, sample_data_df, expected_predictions, tmp_path  # noqa: F811
):  # pylint: disable=redefined-outer-name
    """Test prediction workflow with reporting."""
    # TODO: Test adding saver to flow
    test_run_name = "test_integration_forecast_and_report"
    saver_data = CSVSaver(tmp_path)
    my_model = Prophet(weekly_seasonality=True, daily_seasonality=False)
    mocker.patch.object(my_model, 'fit')
    my_model.fit.return_value = my_model
    mocker.patch.object(my_model, 'predict')
    my_model.predict.return_value = TimeSeries.from_dataframe(
        expected_predictions, time_col=DS_COL, value_cols="yhat"
    )
    forecaster = Forecaster(my_model, savers=[saver_data])

    setting_path = create_settings_file(tmp_path, "[settings]\nSLACK_TOKEN=token")

    slack_report = SlackReportTask("channel_id", "mae", setting_path)
    slack_report.slack_client.files_upload = mocker.stub(name="files_upload")
    # mocker.patch.object(slack_report.slack_client., "files_upload")

    plot_config = deepcopy(PLOT_CONFIG)
    plot_config[ANOMALY_PLOT][MONTHLY_TIME_GRANULARITY][FIG_SIZE] = (8, 3)
    forecast_plotter = ForecastPlotterTask(
        path=tmp_path,
        metric_name='test',
        time_granularity=MONTHLY_TIME_GRANULARITY,
        plot_config=plot_config,
    )

    with SoamFlow(name=test_run_name, saver=None) as f:  # noqa
        preds_model = forecaster(time_series=sample_data_df, output_length=7)
        plot_fn = forecast_plotter(preds_model[1], preds_model[0])
        slack_report(preds_model[0], plot_fn)

    fs = f.run()
    assert 3 == len(fs.result[preds_model]._result.value)
    assert expected_predictions.ds.equals(fs.result[preds_model]._result.value[0].ds)
    assert expected_predictions.yhat.values == pytest.approx(
        fs.result[preds_model]._result.value[0].yhat, 0.1
    )
    assert fs.is_successful()
    plot_filename = str(fs.result[plot_fn]._result.value)
    expected_msg = create_slack_message(expected_predictions, "mae")
    slack_report.slack_client.files_upload.assert_called_once_with(
        channels="channel_id",
        file=plot_filename,
        initial_comment=expected_msg,
        title="mae Forecast",
    )
    assert_saved_data(tmp_path, test_run_name)
