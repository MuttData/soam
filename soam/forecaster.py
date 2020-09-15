# forecaster.py
"""
Forecaster
----------
Is a main class of SoaM. It manages the models, data and storages.
"""

from typing import TYPE_CHECKING, Optional, Tuple

import pandas as pd
from darts import TimeSeries
from darts.models.forecasting_model import ForecastingModel

from soam.constants import DS_COL, FORECAST_DATE, YHAT_COL
from soam.step import Step

if TYPE_CHECKING:
    from soam.savers import Saver


class Forecaster(Step):
    def __init__(self, model: ForecastingModel = None,
                 savers: Optional[Saver] = None, **kwargs):
        """A Forecaster handles models, data and storages.

        Parameters
        ----------
        model : darts.models.forecasting_model.ForecastingModel
            The model that will be fitted and execute the predictions.
        savers : soam.savers.Saver
            The saver to store the parameters and state changes.
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:
                self.state_handlers.append(saver.save_forecast)

        self.time_series = pd.DataFrame
        self.prediction = pd.DataFrame
        self.model = model

    def run(self, time_series: pd.DataFrame = None,
            input_length: Optional[int] = 1, output_length: int = 1,
            **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame, ForecastingModel]:
        """Executes the models fit and predict

        Creates a TimeSeries from a pandas DataFrame and stores the
         predictions.

        Parameters
        ----------
        time_series : pandas.DataFrame
            A pandas DataFrame containing as minimum the first column
            with DataTime values, the second column the y to predict
            and the other columns more data
        input_length : int, optional
            TODO: unused parameter, check if its safe to delete.
        output_length : int
            The length of the output
        **kwargs : dict
            Keyword arguments.
            TODO: unused parameter, check if its safe to delete.

        Returns
        -------
        tuple(pandas.DataFrame, Darts.ForecastingModel)
            a tuple containing a pandas DataFrame with the predicted values
            and the trained model.

        Other Parameters
        ----------------
        return_pred : bool, optional
            Whether to return the prediction or not.
            TODO: unused parameter, check if its safe to delete.
        """
        self.time_series = time_series.copy()
        values_columns = self.time_series.columns.to_list()
        values_columns.remove(DS_COL)

        time_series = TimeSeries.from_dataframe(
            self.time_series, time_col=DS_COL, value_cols=values_columns
        )

        # TODO: fix Unexpected argument **kwargs in self.model.fit
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

        return self.prediction, self.time_series, self.model
