# anomaly_detector.py
"""
Anomaly Detector
----------
"""

from typing import (  # pylint:disable=unused-import
    TYPE_CHECKING,
    Dict,
    List,
    Optional,
    Union,
)

import pandas as pd

from soam.constants import DS_COL
from soam.core import Step

if TYPE_CHECKING:
    from soam.savers import Saver


class Anomaly(Step):
    def __init__(  # type: ignore
        self,
        savers: "Optional[List[Saver]]" = None,
        ds_col: str = DS_COL,
        value_cols: List = [],
        **kwargs,
    ):
        """Detect anomaly of given value and its boundaries

        Parameters
        savers : list of soam.savers.Saver, optional
            The saver to store the parameters and state changes.
        ds_col: str
            Default DS_COL, label of the DateTime to use as Index
        value_cols: list
            label of the boundaries columns
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:
                self.state_handlers.append(saver.save_forecast)

        self.time_series = pd.DataFrame()
        self.prediction = pd.DataFrame()
        self.value_cols = value_cols
        self.ds_col = ds_col

    def run(  # type: ignore
        self, time_series: pd.DataFrame, prediction: pd.DataFrame, metric: str
    ) -> pd.DataFrame:
        """
        Detect anomaly with forecasted boundaries

        Parameters
        ----------
        time_series: pandas DataFrame
            containing as minimum the first column
            with DataTime values, the second column the y to predict
            and the other columns more data
        prediction: pandas DataFrame
            containing as minimum the first column
            with DataTime values, and the boundaries columns defined by
            value_cols
        metric: str
            metric analyzing

        Returns
        -------
        pandas.DataFrame
            A pandas DataFrame with the outliers columns.
        """

        prediction = prediction[[self.ds_col, *self.value_cols]]
        prediction[self.ds_col] = prediction[self.ds_col].astype("datetime64[ns]")

        time_series = time_series.iloc[-len(prediction) :][[self.ds_col, metric]]
        time_series[self.ds_col] = time_series[self.ds_col].astype("datetime64[ns]")
        outlier = pd.merge_asof(time_series, prediction, on=self.ds_col)
        outlier["default"] = False
        outlier["outlier_lower"] = outlier.default.where(
            outlier[self.value_cols[0]] < outlier[metric], True
        )
        outlier["outlier_upper"] = outlier.default.where(
            outlier[self.value_cols[1]] > outlier[metric], True
        )
        del outlier["default"]

        outlier.columns = [f"{str(col)}_{metric}" for col in outlier.columns]
        outlier = outlier.rename({f"{self.ds_col}_{metric}": self.ds_col}, axis=1)
        outlier = outlier.rename({f"{metric}_{metric}": self.ds_col}, axis=1)

        return outlier
