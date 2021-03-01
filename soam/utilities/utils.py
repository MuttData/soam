# utils.py
"""
Utils
-----
Utility functions for the whole project.
"""
from copy import deepcopy
import logging.config
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from pandas.tseries import offsets

logger = logging.getLogger(__name__)


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


def filter_by_class_or_subclass(l, c):
    return [e for e in l if isinstance(e, c) or issubclass(e.__class__, c)]


def split_backtesting_ranges(
    time_series: pd.DataFrame,
    test_window: int = 1,
    train_window: Optional[int] = 1,
    step_size: int = None,
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """Generates time series partitions for backtesting.

    Parameters
    ----------
    time_series: pd.DataFrame
        Original data used for training and evaluation.
    test_window: int
        Time range steps to be extracted from the end of the original time series.
    train_window: int, optional
        Time range steps to be extracted before the test data.
        If a value is passed then the sliding method will be used to select
         the training data.
        If `None` then the full time series will be used, the expanding window method.
         It will start with the first train window of step_size size.
    step_size: int
        Distance between each successive step between the beginning of each forecasting
         range. If None defaults to test_window.

    Returns
    -------
    list of tuple of pd.DataFrame
        A list of tuples, of train_set and test_set, to be used to train or evaluate
         the model.

    Notes
    -------
    The end of the split is going to be train_window plus a multiple of step_size. So
     some of the last elements of the time series can be not used in the resulting
     splits.

    Raises
    ------
    IndexError
        If the time series is empty, if the test_window or train_window are greater than
         the time series length, or if the step size is lower than 1.

    See Also
    --------
    For Theorical background read: documentation/references###Window_policies
    """
    if step_size is None:
        step_size = test_window

    raise_message = None
    if time_series.empty:
        raise_message = "The time series dataframe is empty."
    elif 0 >= test_window or test_window >= len(time_series):
        raise_message = "Inconsistent test window."
    elif 0 >= step_size:
        raise_message = "Step size should be greater than zero."
    elif train_window is not None and (
        0 >= train_window or train_window >= len(time_series)
    ):
        raise_message = "Inconsistent train window."
    if raise_message:
        raise IndexError(raise_message)

    result_slices = []
    for start_test_pos in range(
        train_window or step_size, len(time_series) - test_window + 1, step_size
    ):
        result_slices.append(
            (
                time_series.iloc[
                    start_test_pos - train_window
                    if train_window
                    else 0 : start_test_pos
                ],
                time_series.iloc[start_test_pos : start_test_pos + test_window],
            )
        )

    return result_slices
