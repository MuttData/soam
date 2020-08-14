# data_models.py

from datetime import datetime
import enum
import logging

from soam.cfg import FORECASTER_VALUES_TABLE, SOAM_RUN_TABLE, STEP_RUNS_TABLE
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


def now_getter():
    return datetime.now()


def get_default_run_name():
    return f"forecast-run-{now_getter().isoformat()}"


Base = declarative_base()


class OracleIdentity(types.UserDefinedType):  # pylint:disable=abstract-method
    def get_dbapi_type(self, dbapi):
        return int

    def get_col_spec(self):
        return "NUMBER GENERATED ALWAYS AS IDENTITY ORDER"


class Identity(types.TypeDecorator):  # pylint:disable=abstract-method

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


class AbstractRunBase(AbstractIDBase):  # pylint: disable=too-few-public-methods
    """Helper class to represent runs of modules or submodules."""

    __abstract__ = True

    params = Column(Text, nullable=False)
    params_hash = Column(Text, nullable=False)


class SoaMRuns(AbstractIDBase):

    __tablename__ = SOAM_RUN_TABLE

    start_datetime = Column(DateTime, nullable=True)
    end_datetime = Column(DateTime, nullable=True)


class StepTypeEnum(enum.Enum):
    e = "exctract"
    pre = "preprocess"
    f = "forecast"
    post = "postprocess"
    c = "custom"


class StepsRuns(AbstractRunBase):

    __tablename__ = STEP_RUNS_TABLE
    __table_args__ = (UniqueConstraint("run_id"),)

    run_id = Column(Integer, ForeignKey(f"{SOAM_RUN_TABLE}.id"), nullable=False)
    step_type = Column(Enum(StepTypeEnum), nullable=False)


class ForecastValues(AbstractIDBase):

    __tablename__ = FORECASTER_VALUES_TABLE
    __table_args__ = (UniqueConstraint("step_run_id", "forecast_date"),)

    step_run_id = Column(Integer, ForeignKey(f"{STEP_RUNS_TABLE}.id"), nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    yhat = Column(Float, nullable=False)
    yhat_lower = Column(Float)
    yhat_upper = Column(Float)
    y = Column(Float, nullable=True)
    trend = Column(Float)
    outlier_value = Column(Float)
    outlier_sign = Column(Float)
