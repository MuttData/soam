"""Prophet model wrapper."""
import logging
from typing import Dict, List, Union

import pandas as pd
from sklearn.base import BaseEstimator

from soam.constants import DS_COL
from soam.models.base import SkWrapper, sk_constructor_wrapper
from soam.utilities.utils import SuppressStdOutStdErr

# pylint:disable=super-init-not-called, no-member

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from fbprophet import Prophet
except ImportError:
    logger.warning("No Prophet support")
    logger.warning("If you want to use it, ´pip install soam[prophet]´")


class SkProphet(SkWrapper):
    """Scikit-Learn Prophet model wrapper."""

    @sk_constructor_wrapper(Prophet)
    def __init__(
        self,
        extra_seasonalities: List[Dict] = None,
        extra_regressors: List[Union[str, Dict]] = None,
        fit_params: Dict = None,
        ds_col: str = DS_COL,
        full_output: bool = False,
    ):
        """Constructor with extra parameters in addition to the Prophet ones.

        Parameters
        ----------
        extra_seasonalities : List[Dict], optional
            Extra seasonalities for Prophet model, by default None
        extra_regressors : List[Union[str, Dict]], optional
            Extra regressor columns for Prophet model, by default None
        fit_params : Dict, optional
            Parameters for Prophet's fit() call, by default None
        ds_col : str, optional
            Date column name, by default None
        full_output : bool, default False
            Return full Prophet output or just prediction column.
        """
        self.extra_seasonalities = extra_seasonalities
        self.extra_regressors = extra_regressors
        self.fit_params = fit_params
        self.ds_col = ds_col
        self.full_output = full_output
        self.model = BaseEstimator()

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Fit estimator to data."""
        self.model = self._init_sk_model(Prophet, clean=True)
        self._add_extra_params()
        df = self._transform_to_input_format(X, y)
        with SuppressStdOutStdErr():
            if self.fit_params is None:
                self.fit_params = {}
            self.model.fit(df, **self.fit_params)
        return self

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Scikit learn's predict."""
        X = self._transform_to_input_format(X)
        predictions = self.model.predict(X)
        predictions = self._transform_to_output_format(predictions)
        return predictions

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Scikit learn's transform"""
        return self.predict(X)

    def fit_transform(self, X: pd.DataFrame, y: pd.Series):
        """Scikit learn's fit_transform"""
        self.fit(X, y)
        return self.transform(X)

    def _transform_to_output_format(self, predictions: pd.Series) -> pd.DataFrame:
        """Transform Prophet output to SoaM format."""
        predictions.reset_index(drop=True, inplace=True)
        if self.ds_col != DS_COL:
            predictions.rename({"ds": self.ds_col}, axis=1, inplace=True)
        if self.full_output:
            return predictions
        return predictions[[self.ds_col, "yhat"]]

    def _transform_to_input_format(
        self, X: pd.DataFrame, y: pd.Series = None
    ) -> pd.DataFrame:
        """Transform input to Prophet compatible df."""
        if self.ds_col != DS_COL:
            X.rename({self.ds_col: "ds"}, axis=1, inplace=True)
        if y is not None:
            return X.assign(**{"y": y})
        return X

    def _add_extra_params(self) -> None:
        """Add regressors and seasonalities to Prophet model."""
        if self.extra_regressors is not None:
            for regressor in self.extra_regressors:
                if isinstance(regressor, str):
                    self.model.add_regressor(regressor)
                else:
                    self.model.add_regressor(**regressor)

        if self.extra_seasonalities is not None:
            for seasonality in self.extra_seasonalities:
                self.model.add_seasonality(**seasonality)
