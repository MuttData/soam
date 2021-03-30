# data_models.py
"""
Data models
-----------
Contains the data models for SQLAlchemy used in the DBSaver.

See Also
--------
savers.DBSaver : Saver used to store data and parameters in a database.
"""
from datetime import datetime
import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.types as types
from sqlalchemy.types import TIMESTAMP
from sqlalchemy_utils.types.uuid import UUIDType

from soam.cfg import FORECASTER_VALUES_TABLE, SOAM_FLOW_RUN_TABLE, SOAM_TASK_RUNS_TABLE
from soam.constants import TIMESTAMP_COL


def now_getter() -> datetime:
    """Wrapper for datetime.now()
    TODO: check why we need this wrapper.

    Returns
    -------
    datetime
        The current datetime.
    """
    return datetime.now()


def get_default_run_name() -> str:
    """Obtains a run name that contains the current datetime.
    TODO: unused function.

    Returns
    -------
    str
        A concatenated string of 'forecast-run-' and the current datetime
        in isoformat
    """
    return f"forecast-run-{now_getter().isoformat()}"


Base = declarative_base()
# TODO: The rest of this file is not checked to be numpydoc complaint.


class OracleIdentity(types.UserDefinedType):  # pylint:disable=abstract-method
    """
    This column is a column type defined for the creation of autonumeric indices for the Oracle specific implementation.
    """

    def get_dbapi_type(self, dbapi):
        return int

    def get_col_spec(self):
        return "NUMBER GENERATED ALWAYS AS IDENTITY ORDER"


class Identity(types.TypeDecorator):  # pylint:disable=abstract-method
    """
    Creates an identity object intended to represent an autonumeric column which calls dialect specific implementations.
    """

    impl = Integer

    def load_dialect_impl(self, dialect):
        if dialect.name == "oracle":
            return dialect.type_descriptor(OracleIdentity)
        return dialect.type_descriptor(self.impl)

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value


class AbstractIDBase(Base):  # type: ignore # pylint: disable=too-few-public-methods
    """Helper class to add primary keys."""

    __abstract__ = True

    id = Column(Identity, primary_key=True)


class SoamFlowRunSchema(Base):  # type: ignore
    """Soam Flow Run Schema Generation"""

    __tablename__ = SOAM_FLOW_RUN_TABLE

    flow_run_id = Column(UUIDType(binary=False), primary_key=True)
    run_date = Column(DateTime, nullable=True)
    start_datetime = Column(DateTime, nullable=True)
    end_datetime = Column(DateTime, nullable=True)


class StepTypeEnum(enum.Enum):
    extract = "extract"
    preprocess = "preprocess"
    forecast = "forecast"
    postprocess = "postprocess"
    custom = "custom"


# Be aware when droping the table you will have to manually drop the type,
# it persist after droping the table:
# DROP TYPE steptypeenum;


class SoamTaskRunSchema(Base):  # type: ignore
    """Soam Task Run Schema Generation"""

    __tablename__ = SOAM_TASK_RUNS_TABLE

    params = Column(Text, nullable=False)
    params_hash = Column(Text, nullable=False)

    task_run_id = Column(UUIDType(binary=False), primary_key=True)
    flow_run_id = Column(
        UUIDType(binary=False),
        ForeignKey(f"{SOAM_FLOW_RUN_TABLE}.flow_run_id"),
        nullable=True,
    )
    step_type = Column(Enum(StepTypeEnum), nullable=False)


class ForecastValues(AbstractIDBase):
    """Forecasted values Table Definition"""

    __tablename__ = FORECASTER_VALUES_TABLE
    __table_args__ = (UniqueConstraint("task_run_id", "forecast_date"),)

    task_run_id = Column(
        UUIDType(binary=False),
        ForeignKey(f"{SOAM_TASK_RUNS_TABLE}.task_run_id"),
        nullable=False,
    )
    forecast_date = Column(DateTime, nullable=False)
    yhat = Column(Float, nullable=False)
    yhat_lower = Column(Float)
    yhat_upper = Column(Float)
    y = Column(Float, nullable=True)
    trend = Column(Float)
    outlier_value = Column(Float)
    outlier_sign = Column(Float)


class AbstractTimeSeriesTable(AbstractIDBase):
    """
    Base table to store time series data.

    This class should be used as base for the table from which timeseries will be
    extracted.
    ```
    class ConcreteTimeSeriesTable(AbstractTimeSeriesTable):
        __tablename__ = "concrete_ts"

        fact_1 = Column(Float)
        dimension_1 = Column()
    ```
    """

    __abstract__ = True
    timestamp = Column(TIMESTAMP_COL, TIMESTAMP, index=True)
