# forecaster.py
"""
Forecaster
----------
"""

from typing import (  # pylint:disable=unused-import
    TYPE_CHECKING,
    Dict,
    List,
    Optional,
    Union,
)

# from pandas.core.common import maybe_make_list
from darts import TimeSeries
import pandas as pd
from prefect.utilities.tasks import defaults_from_attrs

from soam.constants import DS_COL, YHAT_COL
from soam.core import Step
from soam.models.base import BaseModel
from soam.utilities.utils import sanitize_arg_empty_dict

if TYPE_CHECKING:
    from soam.savers import Saver


class Forecaster(Step):
    def __init__(  # type: ignore
        self,
        model: Optional[BaseModel] = None,
        savers: "Optional[List[Saver]]" = None,
        output_length: int = 1,
        model_kwargs: Optional[Dict] = None,
        ds_col: str = DS_COL,
        value_cols: Optional[str] = YHAT_COL,
        drop_after: bool = False,
        **kwargs,
    ):
        """Wraps a forecasting model to run it inside a pipeline.

        Parameters
        model : darts.models.forecasting_model.ForecastingModel
            The model that will be fitted and execute the predictions.
        output_length : int
            The length of the output to predict.
        model_kwargs : dict
            Keyword arguments to be passed to the model when fitting.
        savers : list of soam.savers.Saver, optional
            The saver to store the parameters and state changes.
        ds_col: str
            Default DS_COL, label of the DateTime to use as Index
        value_cols: str, optional
            Default YHAT_COL, label of the columns to forecast
        drop_after: bool
            Default False, if True drop the output_length from the timeseries
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:
                self.state_handlers.append(saver.save_forecast)

        self.model = model
        self.output_length = output_length
        self.model_kwargs = sanitize_arg_empty_dict(model_kwargs)

        self.time_series = pd.DataFrame()
        self.prediction = pd.DataFrame()
        self.value_cols = value_cols
        self.ds_col = ds_col
        self.drop_after = drop_after

    @defaults_from_attrs('output_length', 'model_kwargs')
    def run(  # type: ignore
        self, time_series: pd.DataFrame, output_length=None, model_kwargs=None,
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
        output_length
            The length of the output
        model_kwargs
            Keyword arguments to be passed to the model when fitting.

        Returns
        -------
        tuple(pandas.DataFrame, Darts.ForecastingModel)
            a tuple containing a pandas DataFrame with the predicted values
            and the trained model.
        """
        # TODO: **kwargs should be a dedicated variable for model hyperparams.
        # TODO Check for empty dates and fill them.
        self.time_series = time_series.copy()  # type: ignore
        self.time_series = self.time_series.sort_values(by=self.ds_col)

        time_series = TimeSeries.from_dataframe(
            self.time_series, time_col=self.ds_col, value_cols=self.value_cols,
        )
        if self.drop_after:
            time_series = time_series.drop_after(
                time_series.end_time()
                - pd.Timedelta(output_length - 1, unit=time_series.freq_str())
            )

        if self.drop_after:
            self.time_series = self.time_series[: -self.output_length]
            future = self.time_series[-self.output_length :][[self.ds_col]]
        else:
            future = pd.date_range(
                self.time_series[[self.ds_col]].iloc[-1][0],
                periods=self.output_length,
                name=self.ds_col,
            )

        # TODO: fix Unexpected argument **kwargs in self.model.fit
        self.model.fit(self.time_series, y=self.value_cols, **model_kwargs)  # type: ignore
        self.prediction = self.model.predict(future)  # type: ignore

        # self.prediction.reset_index(level=0, inplace=True)
        # self.prediction.rename(
        #    columns={
        #        self.prediction.columns[0]: self.ds_col,
        #    },
        #    inplace=True,
        # )

        return self.prediction, self.time_series, self.model
