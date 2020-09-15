# utils.py
"""
Utils
----------
Utility functions for the whole project.
"""
import logging.config
from copy import deepcopy
from pathlib import Path

import pandas as pd
from pandas.tseries import offsets

from soam.constants import PARENT_LOGGER

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


def range_datetime(datetime_start, datetime_end, hourly_offset: bool = False,
                   timeskip=None, as_datetime: bool = False):
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
