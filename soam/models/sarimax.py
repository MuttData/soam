"""statsmodels.SARIMAX estimators."""
import logging
from typing import Dict, List, Tuple

import pandas as pd

from soam.constants import DS_COL, YHAT_COL
from soam.models.base import SkWrapper, sk_constructor_wrapper

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
except ImportError:
    logger.warning("No SARIMAX support")
    logger.warning("If you want to use it, ´pip install soam[statsmodels]´")


class SkSarimax(SkWrapper):
    """Scikit-Learn statsmodels.SARIMAX model wrapper."""

    @sk_constructor_wrapper(SARIMAX)
    def __init__(  # pylint: disable=super-init-not-called
        self,
        extra_regressors: List[str] = None,
        fit_params: Dict = None,
        date_col: str = DS_COL,
    ):
        """Construct wrapper with extra parameters in addition to the SARIMAX ones.

        Parameters
        ----------
        extra_regressors : List[str], optional
            Column names of exogenous variables, by default None
        fit_params : Dict, optional
            Params to be fed to model's .fit() method, by default None
        date_col : str, optional
            date column, by default None
        """
        self.extra_regressors = extra_regressors
        self.fit_params = fit_params or {}
        self.date_col = date_col

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """
        Fit estimator to data.

        Notes:
            Since SARIMAX requires endog and exog arrays (not colnames) at
            init time, we transform the input before _init_sk_model.
        """
        # arrays are required at model initialization

        (
            self.exog,  # pylint: disable=attribute-defined-outside-init
            self.endog,  # pylint: disable=attribute-defined-outside-init
        ) = self._transform_to_input_format(X, y)
        self.model = self._init_sk_model(  # pylint: disable=attribute-defined-outside-init
            SARIMAX, clean=True
        )

        self.model_fit = self.model.fit(  # pylint: disable=attribute-defined-outside-init
            **self.fit_params or {}
        )
        # saving as prediction start point
        self._train_len = len(X)  # pylint: disable=attribute-defined-outside-init
        return self

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Scikit learn's predict."""
        exog_predict, _ = self._transform_to_input_format(X)
        start = self._train_len
        end = start + X.pipe(len) - 1
        predictions = self.model_fit.predict(start, end, exog=exog_predict)
        predictions = self._transform_to_output_format(predictions, X)
        return predictions.reset_index(drop=True)

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
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Transform input to SARIMAX compatible format.

        Notes:
            Since SARIMAX only takes arrays as x,y inputs,
            we select the extra_regressors cols from X.
        """

        if self.extra_regressors is not None:
            return X[self.extra_regressors], y
        else:
            return None, y

    def _transform_to_output_format(
        self, predictions: pd.Series, X_pred: pd.DataFrame
    ) -> pd.DataFrame:
        """Transform SARIMAX output to SoaM format."""
        final_predictions = pd.DataFrame()
        final_predictions[self.date_col] = X_pred[self.date_col].values
        final_predictions[YHAT_COL] = predictions.values

        return final_predictions
