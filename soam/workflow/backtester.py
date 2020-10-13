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
from soam.utilities.utils import split_backtesting_ranges
from soam.workflow.forecaster import Forecaster
from soam.workflow.transformer import DummyDataFrameTransformer, Transformer

if TYPE_CHECKING:
    from soam.plotting import ForecastPlotterTask
    from soam.savers import Saver


logger = logging.getLogger(__name__)


class Backetester(Step):
    """Class to perform backtesting.

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
        **kwargs,
    ):
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

    @defaults_from_attrs(
        'forecaster',
        'preprocessor',
        'forecast_plotter',
        'test_window',
        'train_window',
        'step_size',
        'metrics',
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
        metrics: "Dict[str, Callable]" = None,
    ) -> List[Dict[str, Tuple[Any, Any, Any]]]:
        """Train the model with past data and compute metrics.

        Parameters
        ----------
        time_series: pd.DataFrame
            Data used to train and evaluate the data.
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
            prediction, _, _ = fc.run(ready_train_set, output_length=test_window)

            train_start = train_set[DS_COL].min()
            train_end = train_set[DS_COL].max()
            test_end = test_set[DS_COL].max()
            slice_rv["ranges"] = (train_start, train_end, test_end)

            ready_test_set = fitted_preproc.transform(test_set)
            slice_metrics = compute_metrics(
                ready_test_set[Y_COL], prediction[YHAT_COL], metrics
            )
            slice_rv["metrics"] = slice_metrics

            if forecast_plotter:
                full_set = pd.concat([ready_train_set, ready_test_set])
                fcp = forecast_plotter.copy()
                fcp.path = (
                    fcp.path.parent
                    / f"train_start={train_start}_train_end={train_end}_test_end={test_end}_{fcp.path.name}"
                )
                slice_rv["plot"] = fcp.run(full_set, prediction)

            rv.append(slice_rv)
        return rv


def compute_metrics(y_true, y_pred, metrics):
    return {metric_name: func(y_true, y_pred) for metric_name, func in metrics.items()}
