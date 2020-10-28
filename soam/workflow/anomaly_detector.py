"""
Anomaly Detector
----------
"""

from typing import (  # pylint:disable=unused-import
    TYPE_CHECKING,
    List,
    Optional,
    Tuple,
    Union,
)

import pandas as pd
from pandas.core.common import maybe_make_list

from soam.constants import DS_COL
from soam.core import Step

if TYPE_CHECKING:
    from soam.savers import Saver


class Anomaly(Step):
    def __init__(  # type: ignore
        self,
        savers: "Optional[List[Saver]]" = None,
        ds_col: str = DS_COL,
        keep_cols: Union[str, List[str]] = [],
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
        self.keep_cols = maybe_make_list(keep_cols)
        self.ds_col = ds_col

    def run(  # type: ignore
        self, forecasted: Tuple[pd.DataFrame, pd.DataFrame]
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

        Returns
        -------
        pandas.DataFrame
            A pandas DataFrame with the outliers columns.
        """
        time_series = forecasted[1]
        prediction = forecasted[0]

        prediction = prediction[[self.ds_col, *self.value_cols]]
        prediction[self.ds_col] = prediction[self.ds_col].astype("datetime64[ns]")

        metric = set(time_series.columns) - set(self.keep_cols)
        metric = metric - set([self.ds_col])
        if len(metric) != 1:
            raise ValueError(
                f"Bad configuration on Anomaly object: many columns for analyze {metric}"
            )
        metric = metric.pop()

        time_series = time_series.iloc[-len(prediction) :]
        time_series[self.ds_col] = time_series[self.ds_col].astype("datetime64[ns]")
        outlier = pd.merge_asof(time_series, prediction, on=self.ds_col)
        outlier["default"] = False
        outlier[f"outlier_lower_{metric}"] = outlier.default.where(
            outlier[self.value_cols[0]] < outlier[metric], True
        )
        outlier[f"outlier_lower_{metric}"] = outlier.default.where(
            outlier[self.value_cols[1]] > outlier[metric], True
        )
        del outlier["default"]

        # outlier.columns = [f"{str(col)}_{metric}" for col in outlier.columns]
        outlier = outlier.rename(
            columns={self.value_cols[0]: f"{self.value_cols[0]}_{metric}"}
        )
        outlier = outlier.rename(
            columns={self.value_cols[1]: f"{self.value_cols[1]}_{metric}"}
        )

        return outlier
