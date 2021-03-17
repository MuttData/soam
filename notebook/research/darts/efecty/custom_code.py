"""Darts performance metrics and fortnights generation"""
from typing import Callable

from darts import TimeSeries, metrics
import numpy as np
import pandas as pd


@metrics.metrics.multivariate_support
def sumape(
    actual_series: TimeSeries,
    pred_series: TimeSeries,
    intersect: bool = True,
    reduction: Callable[  # pylint:disable=unused-argument
        [np.ndarray], float
    ] = np.mean,
) -> float:
    """ Sum of Mean Absolute Percentage Error (SuMAPE).
    Given a time series of actual values :math:`y_t` and a time series of predicted values :math:`\\hat{y}_t`
    both of length :math:`T`, it is a percentage value computed as
    TODO: SuMAPE function
    Parameters
    ----------
    actual_series
        The series of actual values
    pred_series
        The series of predicted values
    intersect
        For time series that are overlapping in time without having the same time index, setting `intersect=True`
        will consider the values only over their common time interval (intersection in time).
    reduction
        Function taking as input a np.ndarray and returning a scalar value. This function is used to aggregate
        the metrics of different components in case of multivariate TimeSeries instances.
    Returns
    -------
    float
        The SUM of Mean Absolute Percentage Error (SuMAPE)
    """

    (
        y_true,
        y_hat,
    ) = metrics.metrics._get_values_or_raise(  # pylint:disable=protected-access
        actual_series, pred_series, intersect
    )

    return (np.abs(y_hat - y_true).sum() / (np.abs(y_true) + np.abs(y_hat)).sum()) * 100


def create_fortnights(start_date, end_date):
    """Fortnights generation"""
    dates = pd.date_range(start=start_date, end=end_date).to_series()

    fortnights = (
        dates.groupby(
            [
                dates.dt.year.values,
                dates.dt.month.values,
                np.select(
                    [dates.dt.day <= 15, dates.dt.day > 15],
                    ["1ra_quincena", "2da_quincena"],
                ),
            ]
        )
        .tail(1)
        .values
    )
    fortnights = pd.DataFrame({"holiday": "fortnights", "ds": fortnights})

    return fortnights
