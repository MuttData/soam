# forecaster.py
"""
Forecaster
----------
`Forecaster` is a main class of `SoaM`. It handle everything of the forecast task.
"""

# import logging
from typing import Optional

from darts import TimeSeries
from darts.models.forecasting_model import ForecastingModel
import pandas as pd
from soam.constants import FORECAST_DATE, YHAT_COL

# logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


class Forecaster:
    def __init__(self, model: ForecastingModel):
        """
        A Forecaster is an object that is meant to handle models, data and storages.
        
        Parameters
        ----------
        model
            A darts ForecastingModel that will by fitted and execute the predictions.
        """
        self.raw_series = pd.DataFrame
        self.prediction = pd.DataFrame
        self.model = model

    def run(
        self,
        raw_series: pd.DataFrame = None,
        input_length: Optional[int] = 1,
        output_length: int = 1,
        *args,
        **kwargs
    ) -> pd.DataFrame:
        """
        Execute fit and predict with Darts models,
        creating a TimeSeries from a pandas DataFrame
        and storing the prediction with in the object.

        Parameters
        ----------
        raw_series
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
        pandas.DataFrame
            Optionally, pandas DataFrame containing the predicted values.
        """
        DATETIME_COLUM = "ds"
        self.raw_series = raw_series.copy()
        values_columns = self.raw_series.columns.to_list()
        values_columns.remove(DATETIME_COLUM)

        time_series = TimeSeries.from_dataframe(
            self.raw_series, time_col=DATETIME_COLUM, value_cols=values_columns
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

        return self.prediction
