"""statsmodels.holtwinters estimators."""
import logging
from typing import Dict, Tuple

import pandas as pd

from soam.constants import DS_COL, YHAT_COL
from soam.models.base import SkWrapper, sk_constructor_wrapper
from soam.utilities.utils import SuppressStdOutStdErr

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# pylint: disable=super-init-not-called, attribute-defined-outside-init, unnecessary-pass, no-member

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except ImportError:
    logger.warning("No ExponentialSmoothing support")
    logger.warning("If you want to use it, ´pip install soam[statsmodels]´")


class SkExponentialSmoothing(SkWrapper):
    """Scikit-Learn statsmodels.ExponentialSmoothing model wrapper."""

    @sk_constructor_wrapper(ExponentialSmoothing)
    def __init__(
        self, fit_params: Dict = None, date_col: str = DS_COL,
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
        with SuppressStdOutStdErr():

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
        return predictions

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Scikit learn's transform."""
        return self.predict(X)

    def fit_transform(self, X: pd.DataFrame, y: pd.Series, output_length: int = 1):
        """Scikit learn's fit_transform with output_length."""
        X_train = X[:-output_length]
        X_pred = X[-output_length:]
        y_train = y[:-output_length]
        self.fit(X_train, y_train)
        return self.transform(X_pred)

    def _transform_to_input_format(
        self, X: pd.DataFrame, y: pd.Series = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Transform input to ExponentialSmoothing compatible format."""
        # saving as prediction start point
        if y is not None:
            # train
            if self.date_col is not None:
                return pd.Series(y.values, index=X[self.date_col].values)
            return pd.Series(y.values, index=X.index)
        else:
            # predict
            return X.pipe(len), y

    def _transform_to_output_format(
        self, predictions: pd.Series, X_pred: pd.DataFrame
    ) -> pd.DataFrame:
        """Transform ExponentialSmoothing output to SoaM format."""
        final_predictions = pd.DataFrame()
        final_predictions[self.date_col] = X_pred[self.date_col].values
        final_predictions[YHAT_COL] = predictions.values
        return final_predictions
