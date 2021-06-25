"""Workflow backtester."""
from collections.abc import Mapping
import logging
from typing import (  # pylint:disable=unused-import
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import pandas as pd
from prefect.utilities.tasks import defaults_from_attrs

from soam.constants import DS_COL, Y_COL, YHAT_COL
from soam.core import Step
from soam.utilities.utils import add_future_dates, split_backtesting_ranges
from soam.workflow.forecaster import Forecaster
from soam.workflow.transformer import DummyDataFrameTransformer, Transformer

if TYPE_CHECKING:
    from soam.plotting.forecast_plotter import ForecastPlotterTask
    from soam.savers.savers import Saver


logger = logging.getLogger(__name__)
RANGES_KEYWORD = "ranges"
METRICS_KEYWORD = "metrics"
PLOT_KEYWORD = "plot"
DEFAULT_METRIC_AGGREGATION = {
    "avg": lambda metric_values: sum(metric_values) / len(metric_values),
    "max": max,
    "min": min,
}


class Backtester(Step):
    """
    Class to perform backtesting.

    Note: To run a single fold backtest, for example to validate the model
    performance in the last run, pass a timeseries with the exact lenght of
    train_window plus test_window.

    Parameters
    ----------
    forecaster : soam.Forecaster
        Forecaster that will be fitted and execute the predictions.
    test_window: pd.Timedelta
        Time range to be extracted from the main timeseries on which the model will be evaluated on each backtesting run.
        If `None` then `forecaster.output_length` is be used.
    train_window: pd.Timedelta, optional
        Time range on which the model will trained on each backtesting run.
        If a pd.Timedelta value is passed then the sliding method will be used to select the training data.
        If `None` then the full time series will be used. This is the expanding window method.
    step_size: int
        Distance between each successive step between the beginning of each forecasting
        range. If None defaults to test_window.
    metrics: dict(str, callable)
        `dict` containing name of a metric and a callable to compute it.
        The callable must conform to the interface used by sklearn for regression metrics:
        https://scikit-learn.org/stable/modules/classes.html#regression-metrics
    savers : list of soam.savers.Saver, optional
        The saver to store the parameters and state changes.
    aggregation: bool or dict
        The expected aggregations for the results.
        If set to true will use the default aggregation, this keeps the last plot,
        and calculates the average, minimum and maximum for the different metrics.
        If it's a dict the PLOT_KEYWORD is expected to be assigned to the index
        of the selected plot. METRICS_KEYWORD is expected to be another dictionary
        containing the name of the aggregation associated with the function to
        aggregate de list of values per metric.
        If aggregation is set to False or None, no aggregation would be performed.
        #TODO: make PLOT_KEYWORD support tuples to pick slices.
    """

    def __init__(
        self,
        forecaster: "Forecaster",
        preprocessor: "Transformer" = None,
        forecast_plotter: "ForecastPlotterTask" = None,
        test_window: "Optional[int]" = 1,
        train_window: "Optional[int]" = 1,
        step_size: "Optional[int]" = None,
        metrics: "Dict[str, Callable]" = None,
        savers: "Optional[List[Saver]]" = None,
        aggregation: Union[str, Dict] = None,
        **kwargs,
    ):
        """
        Backtester object initialization.

        Parameters
        ----------
            forecaster: soam.Forecaster
                Forecaster that will be fitted and execute the predictions.
            preprocessor: soam.Transformer
                Transformer that will be used to preprocess the data, optional and defaults to None.
            forecast_plotter: soam.Plotting.ForecastPlotterTask
                Forecast plotter, optional and defaults to None.
            test_window: pd.Timedelta
                Time range to be extracted from the main timeseries on which the model will be evaluated on each backtesting run.
                If `None` then `forecaster.output_length` is be used.
            train_window: pd.Timedelta
                Time range on which the model will trained on each backtesting run.
                If a pd.Timedelta value is passed then the sliding method will be used to select the training data.
                If `None` then the full time series will be used. This is the expanding window method.
            step_size: int
                Distance between each successive step between the beginning of each forecasting
                range. If None defaults to test_window.
            metrics: dict(str, callable)
                `dict` containing name of a metric and a callable to compute it.
                The callable must conform to the interface used by sklearn for regression metrics:
                https://scikit-learn.org/stable/modules/classes.html#regression-metrics
            savers: list of soam.savers.Saver, optional
                The saver to store the parameters and state changes.
            aggregation: bool or dict
                The expected aggregations for the results.
                If set to true will use the default aggregation, this keeps the last plot,
                and calculates the average, minimum and maximum for the different metrics.
                If it's a dict the PLOT_KEYWORD is expected to be assigned to the index
                of the selected plot. METRICS_KEYWORD is expected to be another dictionary
                containing the name of the aggregation associated with the function to
                aggregate de list of values per metric.
                If aggregation is set to False or None, no aggregation would be performed.
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:  # pylint: disable=unused-variable
                pass
                # self.state_handlers.append(saver.save_step)

        if preprocessor is None:
            preprocessor = DummyDataFrameTransformer()

        self.forecaster = forecaster
        self.preprocessor = preprocessor
        self.forecast_plotter = forecast_plotter
        self.test_window = test_window
        self.train_window = train_window
        self.step_size = step_size
        self.metrics = metrics
        self.aggregation = aggregation

    @defaults_from_attrs(
        'forecaster',
        'preprocessor',
        'forecast_plotter',
        'test_window',
        'train_window',
        'step_size',
        'metrics',
        'aggregation',
    )
    def run(  # type: ignore
        self,
        time_series: pd.DataFrame,
        forecaster: Forecaster = None,
        preprocessor: Transformer = None,
        forecast_plotter: "ForecastPlotterTask" = None,
        test_window: pd.Timedelta = None,
        train_window: Optional[int] = None,
        step_size: Optional[int] = None,
        metrics: Dict[str, Callable] = None,
        aggregation: Union[bool, Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Train the model with past data and compute metrics.

        Parameters
        ----------
        time_series: pd.DataFrame
            Data used to train and evaluate the data.
        forecaster : soam.Forecaster
            Forecaster that will be fitted and execute the predictions.
        preprocessor: Transformer
            Provide an interface to transform pandas DataFrames.
        forecast_plotter: ForecastPlotterTask
            Plot forecasts.
        test_window: pd.Timedelta
            Time range to be extracted from the main timeseries on which the model will
            be evaluated on each backtesting run.
            If `None` then `forecaster.output_length` is be used.
        train_window: pd.Timedelta, optional
            Time range on which the model will trained on each backtesting run.
            If a pd.Timedelta value is passed then the sliding method will be used to
            select the training data.
            If `None` then the full time series will be used. This is the expanding
            window method.
        step_size: int
            Distance between each successive step between the beginning of each
            forecasting
            range. If None defaults to test_window.
        metrics: dict(str, callable)
            `dict` containing name of a metric and a callable to compute it.
            The callable must conform to the interface used by sklearn for regression
            metrics:
            https://scikit-learn.org/stable/modules/classes.html#regression-metrics
        aggregation: bool or dict
            The expected aggregations for the results.
            If set to true will use the default aggregation, this keeps the last plot,
            and calculates the average, minimum and maximum for the different metrics.
            If it's a dict the PLOT_KEYWORD is expected to be assigned to the index
            of the selected plot. METRICS_KEYWORD is expected to be another dictionary
            containing the name of the aggregation associated with the function to
            aggregate de list of values per metric.
            If aggregation is set to False or None, no aggregation would be performed.
            #TODO: make PLOT_KEYWORD support tuples to pick slices.
        """
        # TODO
        # - What is the effect of reusing steps like this if they have saver set?

        if test_window is None:
            test_window = forecaster.output_length  # type: ignore

        time_series_splits = split_backtesting_ranges(
            time_series, test_window, train_window, step_size,
        )
        rv = []
        for train_set, test_set in time_series_splits:
            slice_rv = {}

            fc = forecaster.copy()  # type: ignore
            preproc = preprocessor.copy()  # type: ignore

            ready_train_set, fitted_preproc = preproc.run(train_set)
            ready_train_set = add_future_dates(ready_train_set, periods=test_window)
            prediction, _, _ = fc.run(ready_train_set)
            train_start = train_set[DS_COL].min()
            train_end = train_set[DS_COL].max()
            test_end = test_set[DS_COL].max()
            slice_rv[RANGES_KEYWORD] = (train_start, train_end, test_end)

            ready_test_set = fitted_preproc.transform(test_set)
            slice_metrics = compute_metrics(
                ready_test_set[Y_COL], prediction[YHAT_COL], metrics
            )
            slice_rv[METRICS_KEYWORD] = slice_metrics

            if forecast_plotter:
                full_set = pd.concat([ready_train_set, ready_test_set])
                fcp = forecast_plotter.copy()
                fcp.path = (
                    fcp.path.parent
                    / f"train_start={train_start}_train_end={train_end}_test_end={test_end}_{fcp.path.name}"
                )
                slice_rv[PLOT_KEYWORD] = fcp.run(full_set, prediction)

            rv.append(slice_rv)

        if aggregation:
            return aggregate_rv(aggregation, rv)
        return rv


def aggregate_rv(
    aggregation: Union[bool, Dict], result_values: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Aggregates a list of results from the Backtester.

    Parameters
    ----------
    aggregation: bool or dict
        The expected aggregations for the results.
        If set to true will use the default aggregation, this keeps the last plot,
        and calculates the average, minimum and maximum for the different metrics.
        If it's a dict the PLOT_KEYWORD is expected to be assigned to the index
        of the selected plot. METRICS_KEYWORD is expected to be another dictionary
        containing the name of the aggregation associated with the function to
        aggregate de list of values per metric.
        #TODO: make PLOT_KEYWORD support tuples to pick slices.
    result_values: list of dict of str and any
        List containing the results of the different slices of the backtester.

    Returns
    -------
        #TODO: check if we need to return list for interface compatibility or we can
        #TODO: return just the dict.
        list of dict of str and any
        A list containing one dict with the whole range of the splits, the selected
        plot and the different aggregation functions per metric.
    """
    metric_aggregation = DEFAULT_METRIC_AGGREGATION
    aggregated_plot = result_values[-1][PLOT_KEYWORD]
    if isinstance(aggregation, Mapping):
        if METRICS_KEYWORD in aggregation:
            metric_aggregation = aggregation[METRICS_KEYWORD]
        if PLOT_KEYWORD in aggregation:
            aggregated_plot = result_values[aggregation[PLOT_KEYWORD]][PLOT_KEYWORD]

    metrics_to_aggregate: Dict[str, List] = {}
    for split_result in result_values:
        for metric, value in split_result[METRICS_KEYWORD].items():
            metrics_to_aggregate.setdefault(metric, []).append(value)

    aggregated_metrics = {
        metric: {
            aggregation_name: metric_aggregation[aggregation_name](  # type: ignore
                metrics_to_aggregate[metric]
            )
            for aggregation_name in metric_aggregation.keys()
        }
        for metric in metrics_to_aggregate.keys()
    }

    return [
        {
            RANGES_KEYWORD: (
                result_values[0][RANGES_KEYWORD][0],
                result_values[-1][RANGES_KEYWORD][-1],
            ),
            METRICS_KEYWORD: aggregated_metrics,
            PLOT_KEYWORD: aggregated_plot,
        }
    ]


def compute_metrics(y_true, y_pred, metrics):
    """
    Computation of a given metric

    Parameters
    ----------
    y_true:
        True values for y
    y_pred:
        Predicted values for y.
    metrics: metric
        Chosen performance metric to measure the model capabilities.

    Returns
    -------
    dict
        Performance metric and its value"""
    return {metric_name: func(y_true, y_pred) for metric_name, func in metrics.items()}
