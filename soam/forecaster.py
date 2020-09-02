# forecaster.py
"""
Forecaster
----------
`Forecaster` is a main class of `SoaM`. It handle everything of the forecast task.
"""

from typing import TYPE_CHECKING, List, Optional

from darts import TimeSeries
from darts.models.forecasting_model import ForecastingModel
import pandas as pd
from soam.constants import DS_COL, FORECAST_DATE, YHAT_COL
from soam.step import Step

if TYPE_CHECKING:
    from soam.savers import Saver


class Forecaster(Step):
    def __init__(
        self,
        model: ForecastingModel = None,
        savers: "Optional[Saver]" = None,
        **kwargs,
    ):
        """
        A Forecaster is an object that is meant to handle models, data and storages.

        Parameters
        ----------
        model
            A darts ForecastingModel that will by fitted and execute the predictions.
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:
                self.state_handlers.append(saver.save_forecast)

        self.time_series = pd.DataFrame
        self.prediction = pd.DataFrame
        self.model = model

    def run(
        self,
        time_series: pd.DataFrame = None,
        input_length: Optional[int] = 1,
        output_length: int = 1,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Execute fit and predict with Darts models,
        creating a TimeSeries from a pandas DataFrame
        and storing the prediction with in the object.

        Parameters
        ----------
        time_series
            A pandas DataFrame containing as minimum the first column
            with DataTime values, the second column the y to predict
            and the other columns more data
        input_length
            ?
        output_length
            The length of the output
        return_pred
            Optionally, a boolean value indicating to return the prediction or not.

        Returns
        -------
        tuple(pandas.DataFrame, Darts.ForecastingModel)
            a tuple containing a pandas DataFrame with the predicted values
            and the trained model.
        """

        self.time_series = time_series.copy()
        values_columns = self.time_series.columns.to_list()
        values_columns.remove(DS_COL)

        time_series = TimeSeries.from_dataframe(
            self.time_series, time_col=DS_COL, value_cols=values_columns
        )

        self.model.fit(time_series, **kwargs)
        self.prediction = self.model.predict(output_length).pd_dataframe()

        self.prediction.reset_index(level=0, inplace=True)
        self.prediction.rename(
            columns={
                self.prediction.columns[0]: FORECAST_DATE,
                self.prediction.columns[1]: YHAT_COL,
            },
            inplace=True,
        )

        return (self.prediction, self.model)
