# utils.py

"""Utility functions."""
import hashlib
import logging
import logging.config
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import jinja2
import pandas as pd
from pandas.tseries import offsets

from soam.constants import PARENT_LOGGER

logger = logging.getLogger(f'{PARENT_LOGGER}.{__name__}')


def str_to_datetime(datetime_str):
    """Convert possible date-like string to datetime object."""
    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S.%f",
        "%H:%M:%S.%f",
        "%H:%M:%S",
        "%Y%m%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y%m%d",
        "%Y-%m-%dT%H",
        "%Y%m",
    )
    for ftm in formats:
        try:
            return datetime.strptime(datetime_str, ftm)
        except ValueError:
            if ftm is formats[-1]:
                raise


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


def path_or_string(str_or_path):
    """Load file contents as string or return input str."""
    file_path = Path(str_or_path)
    try:
        if file_path.is_file():
            with file_path.open("r") as f:
                return f.read()
    except OSError:
        pass
    return str_or_path


def make_dirs(dir_path):
    """Add a return value to mkdir."""
    Path.mkdir(Path(dir_path), exist_ok=True, parents=True)
    return dir_path


def hash_str(s, length=8):
    """Hash a string."""
    return hashlib.sha256(s.encode("utf8")).hexdigest()[:length]


def apply_time_bounds(df, sd, ed, ds_col):
    """Filter time dates in a datetime-type column or index."""
    if ds_col:
        rv = df.query(f'{ds_col} >= @sd and {ds_col} <= @ed')
    else:
        rv = df.loc[sd:ed]
    return rv


def normalize_ds_index(df, ds_col):
    """Normalize usage of ds_col as column in df."""
    if ds_col in df.columns:
        return df
    elif ds_col == df.index.name:
        df = df.reset_index().rename(columns={"index": ds_col})
    else:
        raise ValueError(f'No column or index found as "{ds_col}".')
    return df


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


class classproperty:
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


class JinjaTemplateException(Exception):
    """Dummy doc."""


class BadInClauseException(JinjaTemplateException):
    """Dummy doc."""


def template(path_or_str, **kwargs):
    """Create jinja specific template.."""
    environment = jinja2.Environment(
        line_statement_prefix=kwargs.pop("line_statement_prefix", "%"),
        trim_blocks=kwargs.pop("trim_blocks", True),
        lstrip_blocks=kwargs.pop("lstrip_blocks", True),
        **kwargs,
    )
    return environment.from_string(path_or_string(path_or_str))
