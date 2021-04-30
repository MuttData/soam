"""statsmodels.holtwinters estimators."""
import logging
from typing import Dict, Tuple
import warnings

import pandas as pd
from sklearn.model_selection import GridSearchCV, ParameterGrid, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from statsmodels.tsa.holtwinters import (  # pylint: disable=import-error
    ExponentialSmoothing,
)

from soam.constants import (
    DATE_COL,
    DEFAULT_TRAIN_DAYS_LIST,
    DEFAULT_TRAINING_DAYS,
    DEFAULT_TSPLIT_SPLITS,
    DEFAULT_TSPLIT_TEST_SIZE,
    YHAT_COL,
)
from soam.models._base import SkWrapper, sk_constructor_wrapper
from soam.models.metaestimator import DaysSelectorEstimator
from soam.utilities.utils import SuppressStdOutStdErr

# supress model FutureWarnings and ConvergenceWarnings bc FDA
warnings.simplefilter("ignore", category=FutureWarning)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# pylint: disable=super-init-not-called, attribute-defined-outside-init, unnecessary-pass, no-member


class SkExponentialSmoothing(SkWrapper):
    """Scikit-Learn statsmodels.ExponentialSmoothing model wrapper."""

    @sk_constructor_wrapper(ExponentialSmoothing)
    def __init__(
        self, fit_params: Dict = None, date_col: str = DATE_COL,
    ):
        """Construct wrapper with extra parameters in addition to the ExponentialSmoothing ones.

        Parameters
        ----------
        fit_params : Dict, optional
            Params to be fed to model's .fit() method, by default None
        date_col : str, optional
            date column, by default None
        """
        pass

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """
        Fit estimator to data.

        Notes:
            Since ExponentialSmoothing requires endog arrays (not colnames) at
            init time, we transform the input before _init_sk_model.
        """
        # arrays are required at model initialization
        self.endog = self._transform_to_input_format(X, y)
        self.model = self._init_sk_model(ExponentialSmoothing, clean=True)
        with warnings.catch_warnings(), SuppressStdOutStdErr():

            self.model_fit = (
                self.model.fit()
                if self.fit_params is None
                else self.model.fit(**self.fit_params)
            )
        # saving as prediction start point
        self._train_len = len(X)

        return self

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Scikit learn's predict."""
        X_len, _ = self._transform_to_input_format(X)

        start = self._train_len
        end = start + X_len - 1
        predictions = self.model_fit.predict(start, end)
        predictions = self._transform_to_output_format(predictions, X)

        return predictions.reset_index(drop=True)

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Scikit learn's transform."""
        return self.predict(X)

    def fit_transform(self, X: pd.DataFrame, y: pd.Series):
        """Scikit learn's fit_transform."""
        self.fit(X, y)
        return self.transform(X)

    def _transform_to_input_format(
        self, X: pd.DataFrame, y: pd.Series = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Transform input to ExponentialSmoothing compatible format."""
        if y is not None:
            # train
            if self.date_col is not None:
                print(y)
                return pd.Series(y.values, index=X[self.date_col].values)
            return pd.Series(y.values, index=X.index)
        else:
            # predict
            return X.pipe(len), y

    def _transform_to_output_format(
        self, predictions: pd.Series, X_pred: pd.DataFrame
    ) -> pd.DataFrame:
        """Transform Prophet output to SoaM format."""
        final_predictions = pd.DataFrame()
        final_predictions[self.date_col] = X_pred[self.date_col].values
        final_predictions[YHAT_COL] = predictions.values
        return final_predictions


def holtwinters_estimator_factory(**kwargs):
    """Create SkLearn estimator/pipeline for Exponential Smoothing Model.

    Notes:
        Use sorted values, use yhat_only = True
    """
    training_days = kwargs.get('training_days', DEFAULT_TRAINING_DAYS)
    train_days_list = DEFAULT_TRAIN_DAYS_LIST
    if training_days > max(DEFAULT_TRAIN_DAYS_LIST):
        train_days_list = DEFAULT_TRAIN_DAYS_LIST + [training_days]

    exp_smoothing_grid = list(
        ParameterGrid(
            {
                "trend": ["add", "mul", "additive", "multiplicative"],
                "damped_trend": [True, False],
                "seasonal_periods": [None, 7],
                "seasonal": ["add", "mul", "additive", "multiplicative"],
                "date_col": [DATE_COL],
                "freq": ["D"],
            }
        )
    )

    grid = {
        "regressor__estimator_class": [SkExponentialSmoothing],
        "regressor__amount_of_days": train_days_list,
        "regressor__sort_col": [DATE_COL],
        "regressor__estimator_kwargs": exp_smoothing_grid,
    }

    test_size = DEFAULT_TSPLIT_TEST_SIZE
    max_train_size = max(train_days_list) - test_size
    ts_splitter = TimeSeriesSplit(
        n_splits=DEFAULT_TSPLIT_SPLITS,
        max_train_size=max_train_size,
        test_size=test_size,
    )

    pipeline = Pipeline(
        [("regressor", DaysSelectorEstimator(SkExponentialSmoothing, training_days,),)]
    )

    return GridSearchCV(
        pipeline, grid, scoring="explained_variance", cv=ts_splitter, verbose=0
    )


estimator_factory = holtwinters_estimator_factory
