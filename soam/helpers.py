# helpers.py
"""Project specific helper functions."""
import logging
from abc import ABC
from datetime import timedelta
from pathlib import Path

from pandas.tseries import offsets
from sklearn.base import BaseEstimator as AttributeHelperMixin

from soam.utils import (
    hash_str,
    make_dirs,
    str_to_datetime,
    range_datetime,
)
from soam.constants import (
    DAILY_TIME_GRANULARITY,
    HOURLY_TIME_GRANULARITY,
    PARENT_LOGGER,
    TIME_GRANULARITIES,
)
from soam.dbconn import session_scope

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")

RUN_ID_COL = "run_id"


def get_store_dir(base_dir, kpi, prefix, date, end_date=None, sample_size=None):
    """Get parquet cache storage directory."""
    store_dir = base_dir / kpi / prefix
    store_dir /= f"{date:%Y%m%d}{f"-{end_date:%Y%m%d}" if end_date is not None else ""}"
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
    """Create name to store tabular data query outputs."""
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
    """Create figure file-path for given model inputs."""
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
    """Process and correct all respective dates for forecaster."""
    # Check not both future and end date as nulls, assert order
    train_w = forecaster_train_window
    future_w = forecaster_future_window
    m = f"Future ("{future_w}") or train ("{train_w}") windows are not geq 0."
    assert all([future_w > 0, train_w >= 0]), m
    end_date = str_to_datetime(end_date) if isinstance(end_date, str) else end_date
    start_date = end_date - offsets.Day(train_w)
    future_date = end_date + offsets.Day(future_w)
    return start_date, end_date, future_date


def create_anomaly_window_dates(end_date, anomaly_window, time_granularity):
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
    """Insert a dataframe to a list of database connections."""
    for db_cli in db_clients:
        dialect = db_cli.dialect
        if insertion_ids:
            df["insertion_id"] = insertion_ids[dialect]
        if coseries_ids:
            df["coseries_id"] = coseries_ids[dialect]
        logger.debug(f"Writing to {dialect} {table_name} table...")
        db_cli.insert_from_frame(df, table_name, if_exists="append", **kwargs)
        logger.info(f"Inserted {len(df)} records in {dialect} "{table_name}" table.")
    return


class TimeRangeConfiguration(AttributeHelperMixin):
    """Time configurations that should remain constant when reprocessing."""

    def __init__(
        self,
        end_date,
        forecast_train_window,
        forecast_future_window,
        time_granularity,
        anomaly_window,
        end_hour,
    ):
        """Initialize instance.

            end_date (datetime): End of the data to train.
            forecast_train_window (int): Number of days used for training.
            forecast_future_window (int): Number for the forecast.
            time_granularity (string): String values defining a time frequency
                such as "H" or "D".

        Ref: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
        """
        # TODO: Validate time_granularity
        sd, ed, fd = create_forecaster_dates(
            end_date, forecast_train_window, forecast_future_window
        )
        self._start_date, self._end_date, self._future_date = (
            sd,
            ed.replace(hour=end_hour),
            fd,
        )
        self._forecast_train_window = forecast_train_window
        self._forecast_future_window = forecast_future_window
        self._time_granularity = time_granularity
        self._anomaly_window = anomaly_window
        self.validate()
        self._anomaly_window_dates = create_anomaly_window_dates(
            end_date, anomaly_window, time_granularity
        )

    def validate(self):
        """Validate current configuration."""
        assert self._start_date <= self._end_date, logger.error(  # type: ignore
            f"Bad dates passed. Start:{self._start_date}, end:{self._end_date}."
        )
        assert self._end_date <= self._future_date, logger.error(  # type: ignore
            f"Bad dates passed. End:{self._end_date}, future:{self._future_date}."
        )
        assert (
            self._time_granularity in TIME_GRANULARITIES
        ), logger.error(  # type: ignore
            f"Bad time granularity passed:{self._time_granularity}, "
            f"Possible values are: {TIME_GRANULARITIES}\n"
        )

    @property
    def forecast_future_window(self):
        return self._forecast_future_window

    @property
    def forecast_train_window(self):
        return self._forecast_train_window

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        return self._end_date

    @property
    def future_date(self):
        return self._future_date

    @property
    def anomaly_window(self):
        return self._anomaly_window

    @property
    def time_granularity(self):
        return self._time_granularity

    @property
    def anomaly_window_dates(self):
        return self._anomaly_window_dates

    def is_hourly(self):
        return self.time_granularity == HOURLY_TIME_GRANULARITY

    def is_daily(self):
        return self.time_granularity == DAILY_TIME_GRANULARITY


class AbstractAnalisysRun(AttributeHelperMixin, ABC):
    """Helper class to represent generic analyses."""

    run_id_col = RUN_ID_COL

    @property
    def db_run_class(self):
        """Returns SA class representing the current run."""
        raise NotImplementedError("Subclasses should implement this!")

    @property
    def db_value_class(self):
        """Returns SA class representing each of the produced values."""
        raise NotImplementedError("Unused method. Check save_children.")

    def get_children_data(self):
        """Returns DataFrame to be stored as results of this run.

        Returns:
            DataFrame with the columns specified by `self.db_value_class`.
        """

        raise NotImplementedError("Unused method. Check save_children.")

    def save_children(self, sess, run_id):
        """Get DataFrame with generated values

        Note:
            Override this method to implent saving mechanisms to save more complex results.

        Args:
            sess: SA session used to save children.
            run_id: DB id of the the parent run.
        """
        analysis_values_df = self.get_children_data()
        analysis_values_df[self.run_id_col] = run_id
        sess.bulk_insert_mappings(
            self.db_value_class, analysis_values_df.to_dict(orient="records")
        )

    def get_run_obj(self):
        """Generate SA object representing current run.

        Returns:
            Instance of SA object representing the current class.
        """
        params_repr = repr(self)
        run_obj = self.db_run_class(
            params=params_repr, params_hash=hash_str(params_repr)
        )
        return run_obj

    def save(self, db_cli_d):
        """Save current run and generated values.

        Args:
            db_cli_d: Dict of dbcon clients used to save the results.

        Returns:
            List of DB ids of each inserted run instance, one for each db client.
        """
        run_ids = {}
        for db_name, db_cli in db_cli_d.items():
            with session_scope(db_cli.get_engine()) as sess:
                run_obj = self.get_run_obj()
                logger.info(f"We will now insert {run_obj} data.")
                sess.add(run_obj)
                sess.flush()
                run_id = run_obj.id
                self.save_children(sess, run_id)
                run_ids[db_name] = run_obj.id

        return run_ids
