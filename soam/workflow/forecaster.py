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
    Tuple,
)

from darts import TimeSeries
from darts.models.forecasting_model import ForecastingModel
import pandas as pd
from prefect.utilities.tasks import defaults_from_attrs

from soam.constants import DS_COL, YHAT_COL
from soam.core import Step
from soam.utilities.utils import sanitize_arg_empty_dict

if TYPE_CHECKING:
    from soam.savers import Saver


class Forecaster(Step):
    def __init__(  # type: ignore
        self,
        model: Optional[ForecastingModel] = None,
        savers: "Optional[List[Saver]]" = None,
        output_length: int = 1,
        model_kwargs: Optional[Dict] = None,
        **kwargs
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
        self.time_series = time_series.copy()  # type: ignore
        values_columns = self.time_series.columns.to_list()
        values_columns.remove(DS_COL)

        time_series = TimeSeries.from_dataframe(
            self.time_series, time_col=DS_COL, value_cols=values_columns
        )

        # TODO: fix Unexpected argument **kwargs in self.model.fit
        self.model.fit(time_series, **model_kwargs)  # type: ignore
        self.prediction = self.model.predict(output_length).pd_dataframe()  # type: ignore

        self.prediction.reset_index(level=0, inplace=True)
        self.prediction.rename(
            columns={
                self.prediction.columns[0]: DS_COL,
                self.prediction.columns[1]: YHAT_COL,
            },
            inplace=True,
        )

        return self.prediction, self.time_series, self.model
