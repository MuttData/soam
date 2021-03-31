# helpers.py
# pylint: skip-file
"""
Utility functions for the project.

TODO: review this file, it seems unused in the rest of the project.
"""
from contextlib import contextmanager
from datetime import timedelta
import logging
from pathlib import Path

from muttlib.utils import make_dirs, str_to_datetime
import numpy as np
import pandas as pd
from pandas.tseries import offsets
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from soam.constants import DS_COL, HOURLY_TIME_GRANULARITY, YHAT_COL
from soam.utilities.utils import range_datetime

logger = logging.getLogger(__name__)

RUN_ID_COL = "run_id"


def get_store_dir(base_dir, kpi, prefix, date, end_date=None, sample_size=None):
    """
    Get parquet cache storage directory.

    Parameters
    ----------
    base_dir: Union[str, Path]
        base directory path
    kpi: str
        key performance indicator being used
    prefix: str
        prefix string
    date: datetime
        datetime
    end_date: datetime
        end datetime
    sample_size: int
        size of the sample

    Returns
    -------
    path
        The new store_dir directory created.
    """
    store_dir = base_dir / kpi / prefix
    store_dir /= f'{date:%Y%m%d}{f"-{end_date:%Y%m%d}" if end_date is not None else ""}'
    if sample_size is not None:
        store_dir /= f"sample-{sample_size}"
    return make_dirs(store_dir)


def get_store_file(
    base_dir,
    kpi,
    date,
    sample_size=None,
    end_date=None,
    prefix=None,
    suffix=None,
    ft="pkl",
    extra_dir=None,
    end_date_hour=False,
):
    """
    Create name to store tabular data query outputs.

    Parameters
    ----------

    base_dir: Union[str, Path]
        base directory path.
    kpi: str
        key performance indicator being used.
    date: datetime
        datetime.
    sample_size: int
        size of the sample
    end_date: datetime
        end datetime.
    prefix: str
        prefix string.
    suffix: str
        suffix string.
    ft: str
        file extension, by default is "pkl" for pickle files.
    extra_dir: str
        extra directory.
    end_date_hour: boolean
        boolean value to determine if the end date hour should be included. False by default.

    Returns
    -------
    path
        path of the store file.
    """
    save_dir = base_dir / kpi
    if extra_dir is not None:
        save_dir /= extra_dir
    save_dir = make_dirs(save_dir)
    outf = f"{date:%Y%m%d}"
    if end_date is not None:
        outf += f"_{end_date:%Y%m%d}"
        if end_date_hour:
            outf += f"T{end_date:%H}"
    if sample_size is not None:
        outf += f"_sample-{sample_size}"
    if prefix is not None:
        outf = f"{prefix}_{outf}"
    if suffix is not None:
        outf = f"{outf}_{suffix}"
    if ft is not None:
        outf += f".{ft}"
    return save_dir / outf


def get_figure_full_path(
    fig_dir,
    target_col,
    fig_name,
    start_date,
    end_date,
    time_granularity,
    granularity,
    suffix=None,
    as_posix=True,
    end_date_hour=False,
):
    """
    Create figure file-path for given model inputs.

    Parameters
    ----------
    fig_dir: path
        figure directory.
    target_col
        target column.
    fig_name: str
        name of the figure
    start_date: date
        start date of analysis.
    end_date: date
        end date of analysis
    time_granularity: str
        time granularity, how much a period represents.
    granularity: str
        granularity.
    suffix: str
        suffix string.
    as_posix: boolean
        True by default.
    end_date_hour: boolean
        boolean value to determine if the end date hour should be included. False by default.

    Returns
    -------
    path
        Path of the created figure.
    """
    save_dir = make_dirs(fig_dir / granularity / time_granularity / fig_name)
    root_name = f"{start_date:%Y%m%d}_{end_date:%Y%m%d}"
    if end_date_hour:
        root_name += f"T{end_date:%H}"
    root_name += f"_{target_col}"
    if suffix is not None:
        root_name += f"_{suffix}"
    fig_path = Path(save_dir, root_name + ".png")
    if as_posix:
        return fig_path.as_posix()
    return fig_path


def create_forecaster_dates(
    end_date, forecaster_train_window, forecaster_future_window
):
    """
    Process and correct all respective dates for forecaster.

    Parameters
    ----------
    end_date: date
        end date of analysis
    forecaster_train_window
        window of the train set to train the forecaster.
    forecaster_future_window
        future time window to predict the target variable value for.

    Returns
    -------
    date
        forecaster dates.
    """
    # Check not both future and end date as nulls, assert order
    train_w = forecaster_train_window
    future_w = forecaster_future_window
    m = f'Future ("{future_w}") or train ("{train_w}") windows are not geq 0.'
    assert all([future_w > 0, train_w >= 0]), m
    end_date = str_to_datetime(end_date) if isinstance(end_date, str) else end_date
    start_date = end_date - offsets.Day(train_w)
    future_date = end_date + offsets.Day(future_w)
    return start_date, end_date, future_date


def create_anomaly_window_dates(end_date, anomaly_window, time_granularity):
    """
    Creation of the anomaly window dates.

    Parameters
    ----------
    end_date: date
        end date of analysis
    anomaly_window
        window time to analyze anomalies.
    time_granularity
        time granularity, how much a period represents.

    Returns
    -------
    list
        anomaly window dates.
    """
    hourly_offset = True if time_granularity == HOURLY_TIME_GRANULARITY else False
    end_date = str_to_datetime(end_date) if isinstance(end_date, str) else end_date
    anomaly_window_start_date = end_date - timedelta(days=(anomaly_window - 1))
    return list(
        range_datetime(
            anomaly_window_start_date,
            end_date,
            hourly_offset=hourly_offset,
            as_datetime=False,
        )
    )


def insert_df_multiple_clients(
    db_clients, insertion_ids, table_name, df, coseries_ids=None, **kwargs
):
    """
    Insert a dataframe to a list of database connections.

    Parameters
    ----------
    db_clients
        clients database
    insertion_ids
        ids to insert data in.
    table_name: str
        name of the table
    df: pd.DataFrame
        pandas dataframe to insert in database.
    coseries_ids=None
    """

    for db_cli in db_clients:
        dialect = db_cli.dialect
        if insertion_ids:
            df["insertion_id"] = insertion_ids[dialect]
        if coseries_ids:
            df["coseries_id"] = coseries_ids[dialect]
        logger.debug(f"Writing to {dialect} {table_name} table...")
        db_cli.insert_from_frame(df, table_name, if_exists="append", **kwargs)
        logger.info(f'Inserted {len(df)} records in {dialect} "{table_name}" table.')
    return


# TODO remove this function when added to muttlib
@contextmanager
def session_scope(engine: Engine, **session_kw):
    """
    Provide a transactional scope around a series of operations.

    Parameters
    ----------
    engine: Engine
        engine connection to the session.
    """

    Session = sessionmaker(bind=engine)
    session = Session(**session_kw)

    try:
        yield session
        session.commit()
    except Exception as err:
        logger.exception(err)
        session.rollback()
        raise
    finally:
        session.close()
