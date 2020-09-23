# utils.py
"""
Utils
----------
Utility functions for the whole project.
"""
from copy import deepcopy
import logging.config
from pathlib import Path

import pandas as pd
from pandas.tseries import offsets

from soam.constants import PARENT_LOGGER

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


def range_datetime(
    datetime_start,
    datetime_end,
    hourly_offset: bool = False,
    timeskip=None,
    as_datetime: bool = False,
):
    # TODO: review datetime_start, datetime_end, are datetimes?
    # TODO: timeskip is Tick?
    """Build datetime generator over successive time steps."""
    if timeskip is None:
        timeskip = offsets.Day(1) if not hourly_offset else offsets.Hour(1)
    if not isinstance(datetime_start, pd.Timestamp):
        datetime_start = pd.Timestamp(datetime_start)
    while datetime_start <= datetime_end:
        if as_datetime:
            yield datetime_start.to_pydatetime()
        else:
            yield datetime_start
        datetime_start += timeskip


def sanitize_arg(v, default=None):
    """Sanitize mutable arguments.

    Get a sanitized version of the given argument value to avoid mutability issues.

    The default arg provided is also deepcopied to avoid problems on that part.

    To use replace this:
    ```
    def f(x={}):
        ...
    ```
    With this:
    ```
    def f(x=None):
        x = sanitize_arg(x, {})
    ```

    Args:
        v: Value to check.
        default: Value to set if

    Returns:
        Santized value.
    """
    if default is None:
        default = {}
    if v is None:
        return deepcopy(default)
    else:
        return v


def sanitize_arg_empty_dict(v):
    """Convenience function for `sanitize_arg(v, {})`"""
    return sanitize_arg(v, {})


def get_file_path(path: Path, fn: str) -> Path:
    """Find an available path for a file, using an index prefix."""
    paths = path.glob(f"*_{fn}")
    max_index = max((int(p.name.split("_")[0]) for p in paths), default=-1) + 1
    return path / f"{max_index}_{fn}"


def split_backtesting_ranges(
    time_series: pd.DataFrame,
    test_window: pd.Timedelta,
    train_window: pd.Timedelta = None,
    step_size: pd.Timedelta = 1,
) -> "List[Tuple(pd.DataFrame, pd.DataFrame)]":
    """Generate the indices to partition a time series according for backtesting.

    Parameters
    ----------
    time_series: int
        Data used to train and evaluate the data.
    test_window: int
        Time range to be extracted from the main timeseries on which the model will be evaluated on each backtesting run.
    train_window: Optional[pd.Timedelta]
        Time range on which the model will trained on each backtesting run.
        If a pd.Timedelta value is passed then the sliding method will be used to select the training data.
        If `None` then the full time series will be used. This is the expanding window method.
    step_size: int
        Distance between each successive step between the beggining of each forecasting range.

    Returns
    -------
    list(tuple(train_set, test_set))
        A list of tuples of datasets to be used to train or evaluate the model.
    """
    # Validate data: Time series must be long enough to build at least one index set for backtesting.
    # TODO

    # - Build the splits
    # TODO

    logger.warning("Not implemented")
