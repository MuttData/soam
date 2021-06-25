"""
Forecaster
----------
Forecaster Task that fits a model to series and predicts.
"""
from typing import TYPE_CHECKING, List, Optional, Tuple  # pylint:disable=unused-import

import pandas as pd

from soam.constants import DS_COL, Y_COL
from soam.core import Step

if TYPE_CHECKING:
    from soam.savers.savers import Saver


class Forecaster(Step):
    """Forecaster Task."""

    def __init__(  # type: ignore
        self,
        model,
        savers: "Optional[List[Saver]]" = None,
        output_length: int = 1,
        ds_col: str = DS_COL,
        response_col: str = Y_COL,
        **kwargs,
    ):
        """
        Wrap a forecasting model to run it inside a pipeline.

        Parameters
        ----------
        model : scikit-learn.base.BaseEstimator
            The model that will be fitted and execute the predictions.
        savers : Optional[List[Saver]], optional
            The saver to store the parameters and state changes, by default None
        output_length : int, optional
            The length of the output to predict, by default 1
        ds_col : str, optional
            The date column name of the input time series DataFrame, by default DS_COL
        response_col : str, optional
            The y column name of the input time series DataFrame, by default Y_COL
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:
                self.state_handlers.append(saver.save_forecast)

        self.model = model
        self.output_length = output_length
        self.ds_col = ds_col
        self.response_col = response_col

        self.time_series = pd.DataFrame()
        self.prediction = pd.DataFrame()

    def run(  # type: ignore
        self, time_series: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, object]:
        """
        Execute fit and predict with a given model and time_series DataFrame.

        Parameters
        ----------
        time_series
            A pandas DataFrame containing as minimum the first column
            with DataTime values, the second column the y to predict
            and the other columns more data

        Returns
        -------
        tuple(pandas.DataFrame, pandas.DataFrame, model)
            0 : Predicted Values DataFrame.
            1 : Provided Time Series data (untouched).
            2 : Trained model.
        """
        self.time_series = time_series.copy()

        X, y = self._format_input(time_series)

        X_train = X[: -self.output_length]
        X_pred = X[-self.output_length :]
        y_train = y[: -self.output_length]

        self.model.fit(X_train, y_train)
        self.prediction = self.model.predict(X_pred)
        return self.prediction, self.time_series, self.model

    def _format_input(
        self, time_series: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Transform time series DataFrame into SoaM compatible format.

        Parameters
        ----------
        time_series : pandas.DataFrame

        Returns
        -------
        pandas.DataFrame
            Formatted DataFrame
        """
        if self.ds_col not in time_series.columns:
            raise ValueError(f"{self.ds_col} not present Time Series columns.")
        if self.response_col not in time_series.columns:
            raise ValueError(f"{self.response_col} not present Time Series columns.")
        time_series = time_series.sort_values(by=self.ds_col)
        return (
            time_series.drop(self.response_col, axis=1),
            time_series[self.response_col],
        )
