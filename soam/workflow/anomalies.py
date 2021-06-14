"""
Anomaly detection module.
"""
import logging
from typing import NamedTuple  # pylint:disable=unused-import

import pandas as pd

from soam.constants import DS_COL, YHAT_COL
from soam.core import Step

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class IntervalColumns(NamedTuple):
    lower: str
    upper: str


class ConfidenceIntervalAnomaly(Step):
    def __init__(  # type: ignore
        self,
        metric: str,
        ds_col: str = DS_COL,
        response_col: str = YHAT_COL,
        interval_cols: IntervalColumns = None,
        **kwargs,
    ):
        """Detect anomaly of given value and its boundaries.

        Parameters
        ----------
        metric : str
            metric name to compare to bounds
        ds_col : str, optional
            Date column, by default DS_COL
        keep_cols_pred : Union[str, List[str]], optional
            Name of the prediction column, by default []
        interval_cols : List[str], optional
            Column names for prediction boundaries, by default []
        """
        super().__init__(**kwargs)
        self.metric = metric
        self.time_series = pd.DataFrame()
        self.prediction = pd.DataFrame()
        self.interval_cols = interval_cols or IntervalColumns(
            lower=f"{YHAT_COL}_lower", upper=f"{YHAT_COL}_upper"
        )
        self.response_col = response_col
        self.ds_col = ds_col

    def run(  # type: ignore
        self, prediction: pd.DataFrame, time_series: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Detect anomaly with forecasted boundaries.

        Parameters
        ----------
            prediction: pandas.DataFrame
                containing as minimum the first column
                with DataTime values, and the boundaries columns defined by
                interval_cols
            time_series: pandas.DataFrame
                containing as minimum the first column
                with DataTime values, the second column the y to predict
                and the other columns more data
        Returns
        -------
        pandas.DataFrame
            A pandas DataFrame with the outliers columns.
        """
        prediction = prediction[[self.ds_col, self.response_col, *self.interval_cols]]
        prediction = prediction.astype({self.ds_col: "datetime64[ns]"})

        if self.metric not in time_series.columns:
            raise ValueError(f"Metric {self.metric} not present in time_series.")

        time_series = time_series.iloc[-len(prediction) :]
        time_series = time_series.astype({self.ds_col: "datetime64[ns]"})
        outlier = pd.merge_asof(time_series, prediction, on=self.ds_col)
        outlier["default"] = False
        outlier[f"outlier_lower_{self.metric}"] = outlier.default.where(
            outlier[self.interval_cols.lower] < outlier[self.metric], True
        )
        outlier[f"outlier_upper_{self.metric}"] = outlier.default.where(
            outlier[self.interval_cols.upper] > outlier[self.metric], True
        )
        outlier.drop("default", axis=1, inplace=True)

        metric_lower = f"{self.interval_cols.lower}_{self.metric}"
        metric_upper = f"{self.interval_cols.upper}_{self.metric}"
        outlier = outlier.rename(columns={self.interval_cols.lower: metric_lower})
        outlier = outlier.rename(columns={self.interval_cols.upper: metric_upper})
        logger.info(  # pylint: disable=logging-format-interpolation
            f"""Anomalies calculated for metric: {self.metric}
            with values: y={outlier[self.metric].iloc[0]:.3f},
            prediction_lower={outlier[metric_lower].iloc[0]:.3f},
            prediction_upper={outlier[metric_upper].iloc[0]:.3f}"""
        )
        return outlier


__all__ = ['ConfidenceIntervalAnomaly']
