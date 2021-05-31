"""Orbit model wrapper."""
import logging
from typing import List, Union
import warnings

import pandas as pd
from typing_extensions import Literal

from soam.constants import SEED
from soam.models.base import SkWrapper, sk_constructor_wrapper
from soam.utilities.utils import SuppressStdOutStdErr

# pylint: disable=super-init-not-called, attribute-defined-outside-init, unnecessary-pass, no-member

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from orbit.models.dlt import DLTFull
except ImportError:
    logger.warning("No orbit support")
    logger.warning("If you want to use it, ´pip install soam[orbit]´")


class SkOrbit(SkWrapper):
    """Scikit-Learn Orbit model wrapper."""

    _ignore_params = ["full_output"]

    @sk_constructor_wrapper(DLTFull)
    def __init__(
        self,
        date_col: str = 'date',
        response_col: str = None,
        regressor_col: Union[List[str], str] = None,
        damped_factor: float = 0.8,
        period: int = 1,
        seasonality: int = -1,
        seed: int = SEED,
        chains: int = 1,
        global_trend_option: Literal[
            'flat', 'linear', 'loglinear', 'logistic'
        ] = "linear",
        full_output: bool = False,
    ):
        """Constructor with extra parameters in addition to the base model ones.

        Parameters
        ----------
        response_col : str
            response or y column name
        date_col : str
            date column name
        regressor_col : Union[List[str], str]
            extra regressors column names
        damped_factor : float, optional
            by default 0.8
        period : int, optional
            by default 1
        seasonality : int, optional
            by default -1
        chains : int, optional
            number of chains spawned by PyStan, by default 1
        seed : int, optional
            by default 1
        global_trend_option : Literal[, optional
            by default "linear"
        full_output : bool, default False
            Return full Orbit output or just prediction column.

        Notes:
            Since Orbit manages kwargs for everything, this is awkward for our
            constructor patching strategy, i.e we need explicit arguments in the signature.
            That's why we explicitly specify them in the wrapper's signature,
            and we mark custom params in _to_ignore.

            For more details on model specific parameters check docs.
        """
        pass

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Fit estimator to data."""
        df = self._transform_to_input_format(X, y)
        self.model = self._init_sk_model(DLTFull, ignore_params=self._ignore_params)
        with warnings.catch_warnings(), SuppressStdOutStdErr():
            warnings.simplefilter("ignore")
            self.model.fit(df)
        return self

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Scikit learn's predict."""
        X = self._transform_to_input_format(X)

        predictions = self.model.predict(X)  # pylint: disable=assignment-from-no-return
        predictions = self._transform_to_output_format(predictions)

        return predictions

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Scikit learn's transform."""
        return self.predict(X)

    def fit_transform(self, X: pd.DataFrame, y: pd.Series):
        """Scikit learn's fit_transform."""
        self.fit(X, y)
        return self.transform(X)

    def _transform_to_input_format(
        self, X: pd.DataFrame, y: pd.Series = None
    ) -> pd.DataFrame:
        """Transform input to Orbit compatible df."""
        if y is not None:
            # set response col dynamically
            self.response_col = y.name
            return X.assign(**{self.response_col: y})
        return X

    def _transform_to_output_format(self, predictions: pd.Series) -> pd.DataFrame:
        """Transform Orbit output to SoaM format."""
        predictions = predictions.rename(columns={"prediction": "yhat"})
        if self.full_output:
            return predictions
        return predictions[[self.date_col, "yhat"]]
