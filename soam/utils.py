# utils.py

"""Utility functions."""
from copy import deepcopy
from datetime import datetime
import logging
import logging.config

import jinja2
from muttlib.utils import path_or_string
import pandas as pd
from pandas.tseries import offsets
from soam.constants import PARENT_LOGGER

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


def range_datetime(
    datetime_start, datetime_end, hourly_offset=False, timeskip=None, as_datetime=False
):
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
