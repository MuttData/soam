import logging
from typing import (  # pylint:disable=unused-import
    TYPE_CHECKING,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import pandas as pd
from prefect.utilities.tasks import defaults_from_attrs

from soam.constants import DS_COL
from soam.forecaster import Forecaster
from soam.step import Step
from soam.transformer import Transformer
from soam.utils import split_backtesting_ranges

if TYPE_CHECKING:
    from soam.savers import Saver


logger = logging.getLogger(__name__)


class Backetester(Step):
    def __init__(
        self,
        forecaster: Forecaster,
        test_window: "Optional[int]" = 1,
        preprocessor: Transformer = None,
        train_window: "Optional[int]" = 1,
        metrics: "Dict[str, Callable]" = None,
        savers: "Optional[List[Saver]]" = None,
        **kwargs
    ):
        """A Forecaster handles models, data and storages.

        Parameters
        ----------
        forecaster : soam.Forecaster
            Forecaster that will be fitted and execute the predictions.
        test_window: pd.Timedelta
            Time range to be extracted from the main timeseries on which the model will be evaluated on each backtesting run.
        train_window: pd.Timedelta, optional
            Time range on which the model will trained on each backtesting run.
            If a pd.Timedelta value is passed then the sliding method will be used to select the training data.
            If `None` then the full time series will be used. This is the expanding window method.
        metrics: dict(str, callable)
            `dict` containing name of a metric and a callable to compute it.
            The callable must conform to the interface used by sklearn for regression metrics:
            https://scikit-learn.org/stable/modules/classes.html#regression-metrics
        savers : list of soam.savers.Saver, optional
            The saver to store the parameters and state changes.
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:
                self.state_handlers.append(saver.save_step)

        self.forecaster = forecaster
        self.preprocessor = preprocessor
        self.test_window = test_window
        self.train_window = train_window
        self.metrics = metrics

    @defaults_from_attrs(
        'forecaster', 'preprocessor', 'test_window', 'train_window', 'metrics'
    )
    def run(  # type: ignore
        self,
        time_series: pd.DataFrame,
        preprocessor: Transformer = None,
        forecaster: Forecaster = None,
        test_window: pd.Timedelta = None,
        train_window: Optional[pd.Timedelta] = None,
        metrics: "Dict[str, Callable]" = None,
    ) -> Dict:
        """Train the model with past data and compute metrics.

        Parameters
        ----------
        time_series: pd.DataFrame
            Data used to train and evaluate the data.
        """
        # TODO
        # - If test_window is not passed we should use the forecaster ouput_lenght arg instead.
        # - Decide wether to return a dict or a Maybe return a `dict` or a Datafram with metrics.
        # - What is the effect of reusing steps like this if they have saver set?
        # - Implement Preprocessor. Should use the fit/transform API of sklearn.
        # - Should we add a column to select the column that will be used as target (both for training and testing)?
        #   => Better be consistent with the Forecaster.

        time_series_splits = split_backtesting_ranges(
            time_series, test_window, train_window,
        )
        rv = []
        for train_set, test_set in time_series_splits:
            # At this point
            fc = forecaster.copy()
            preproc = preprocessor.copy()

            ready_train_set, fitted_preproc = preproc.run(train_set)
            prediction, _, _ = fc.run(ready_train_set, test_window)

            ready_test_set = fitted_preproc(test_set)
            slice_metrics = compute_metrics(ready_test_set, prediction, metrics)

            train_start = train_set[DS_COL].min()
            train_end = train_set[DS_COL].max()
            test_end = train_set[DS_COL].max()
            rv.append((train_start, train_end, test_end), slice_metrics)
        return rv


def compute_metrics(y_true, y_pred, metrics):
    return {metric_name: func(y_true, y_pred) for metric_name, func in metrics.items()}
