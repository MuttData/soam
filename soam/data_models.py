# data_models.py

import logging
from abc import ABC, abstractmethod
from datetime import datetime

import sqlalchemy.types as types
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from cfg import (
    COSERIES_DIMENSIONS_TABLE,
    COSERIES_RUNS_TABLE,
    COSERIES_SCORES_TABLE,
    COSERIES_VALUES_TABLE,
    DELVER_RUN_FACTOR_CONF_TABLE,
    DELVER_RUN_TABLE,
    DRILL_DOWN_RUNS_TABLE,
    DRILL_DOWN_VALUES_TABLE,
    ENV,
    FORECASTER_RUNS_TABLE,
    FORECASTER_VALUES_TABLE,
    INFLUENCER_RUNS_TABLE,
    INFLUENCER_VALUES_TABLE,
    KPI_TABLE,
    TIMELINE_TABLE,
)
from constants import PARENT_LOGGER

# from constants import PARENT_LOGGER, VARCHAR_BIG, VARCHAR_SMALL
# from utils import classproperty

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


def now_getter():
    return datetime.now()


def get_default_run_name():
    return f"{ENV}-run-{now_getter().isoformat()}"


Base = declarative_base()

# TODOs:
# time_granularity and geo_granularity should be enums or smth similar.


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


"""
class KpiModel(AbstractIDBase):
    __tablename__ = KPI_TABLE
    __table_args__ = (UniqueConstraint('name'),)

    parent_id = Column(Integer, ForeignKey(f'{KPI_TABLE}.id'))
    name = Column(String(VARCHAR_BIG), nullable=False)
    name_spanish = Column(Text)
    description_spanish = Column(Text)
    daily_status = Column(Text)
    national_daily_status = Column(Text)
    provincial_daily_status = Column(Text)
    hourly_status = Column(Text)
    national_hourly_status = Column(Text)
    provincial_hourly_status = Column(Text)
    unit = Column(Text)
    client_type = Column(Text)
    created_at = Column(DateTime, nullable=False, default=now_getter)
    updated_at = Column(DateTime, nullable=False, default=now_getter)
"""
'''
class DelverRunModel(AbstractRunBase):

    __tablename__ = DELVER_RUN_TABLE
    # __table_args__ = (
    #    UniqueConstraint('kpi_id', 'end_date', 'geo_granularity', 'time_granularity'),
    # )

    kpi_id = Column(Integer, ForeignKey(f'{KPI_TABLE}.id'))
    run_name = Column(Text, nullable=False, default=get_default_run_name)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    future_date = Column(DateTime, nullable=False)
    geo_granularity = Column(String(VARCHAR_SMALL), nullable=False)
    time_granularity = Column(String(VARCHAR_SMALL), nullable=False)
    is_promoted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, nullable=False, default=now_getter)


class DelverRunFactorConf(AbstractIDBase):
    """Run for a particular combination of values that form a factor.

    The column `factor_conf` should contain a JSON map indicating the values of each factor used
    in the run.
    """

    __tablename__ = DELVER_RUN_FACTOR_CONF_TABLE
    __table_args__ = (UniqueConstraint('delver_run_id', 'factor_conf'),)

    factor_conf = Column(String(VARCHAR_BIG), nullable=False)
    delver_run_id = Column(
        Integer, ForeignKey(f'{DELVER_RUN_TABLE}.id'), nullable=False
    )
    forecaster_run_id = Column(Integer, ForeignKey(f'{FORECASTER_RUNS_TABLE}.id'))
    influencer_run_id = Column(Integer, ForeignKey(f'{INFLUENCER_RUNS_TABLE}.id'))
    drill_down_run_id = Column(Integer, ForeignKey(f'{DRILL_DOWN_RUNS_TABLE}.id'))
    coseries_run_id = Column(Integer, ForeignKey(f'{COSERIES_RUNS_TABLE}.id'))
'''


class ForecasterRuns(AbstractRunBase):

    __tablename__ = FORECASTER_RUNS_TABLE


class ForecasterValues(AbstractIDBase):

    __tablename__ = FORECASTER_VALUES_TABLE
    __table_args__ = (UniqueConstraint("run_id", "forecast_date"),)

    run_id = Column(Integer, ForeignKey(f"{FORECASTER_RUNS_TABLE}.id"), nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    yhat = Column(Float, nullable=False)
    yhat_lower = Column(Float, nullable=False)
    yhat_upper = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    trend = Column(Float, nullable=False)
    outlier_value = Column(Float)
    outlier_sign = Column(Float)


"""
class InfluencerRuns(AbstractRunBase):

    __tablename__ = INFLUENCER_RUNS_TABLE


class InfluencerValues(AbstractIDBase):

    __tablename__ = INFLUENCER_VALUES_TABLE
    __table_args__ = (UniqueConstraint('run_id', 'analysis_date', 'influencer'),)

    run_id = Column(Integer, ForeignKey(f'{INFLUENCER_RUNS_TABLE}.id'), nullable=False)
    analysis_date = Column(DateTime, nullable=False)
    influencer = Column(String(VARCHAR_SMALL), nullable=False)
    influencer_spanish = Column(Text, nullable=False)
    importance = Column(Float, nullable=False)


class DrillDownRuns(AbstractRunBase):

    __tablename__ = DRILL_DOWN_RUNS_TABLE


class DrillDownValues(AbstractIDBase):

    __tablename__ = DRILL_DOWN_VALUES_TABLE
    __table_args__ = (
        UniqueConstraint(
            'run_id',
            'analysis_date',
            'influencer',
            'influencer_value_range',
            'kpi_variable',
            'kpi_variable_value',
        ),
    )

    run_id = Column(Integer, ForeignKey(f'{DRILL_DOWN_RUNS_TABLE}.id'), nullable=False)
    analysis_date = Column(DateTime, nullable=False)
    influencer = Column(String(VARCHAR_SMALL), nullable=False)
    influencer_value_range = Column(String(VARCHAR_BIG), nullable=False)
    kpi_variable = Column(String(VARCHAR_SMALL), nullable=False)
    kpi_variable_value = Column(Float, nullable=True)
    kpi_variable_overall_avg = Column(Float, nullable=True)
    user_share = Column(Float, nullable=True)
    insight = Column(Text, nullable=True)
"""


class CoseriesRuns(AbstractRunBase):

    __tablename__ = COSERIES_RUNS_TABLE


class CoseriesDimensions(AbstractIDBase):

    __tablename__ = COSERIES_DIMENSIONS_TABLE
    run_id = Column(Integer, ForeignKey(f"{COSERIES_RUNS_TABLE}.id"), nullable=False)
    dimension = Column(Text, nullable=False)
    y_col = Column(Text, nullable=False)


class CoseriesValues(AbstractIDBase):
    """Represents a Coseries value.

    Note that this is common among all coseries runs.
    """

    __tablename__ = COSERIES_VALUES_TABLE
    __table_args__ = (UniqueConstraint("dimension_id", "value_datetime"),)

    dimension_id = Column(
        Integer, ForeignKey(f"{COSERIES_DIMENSIONS_TABLE}.id"), nullable=False
    )
    value_datetime = Column(DateTime, nullable=False)
    y = Column(Float, nullable=False)


class CoseriesScores(AbstractIDBase):

    __tablename__ = COSERIES_SCORES_TABLE
    __table_args__ = (UniqueConstraint("run_id", "dimension_id", "analysis_datetime"),)

    run_id = Column(Integer, ForeignKey(f"{COSERIES_RUNS_TABLE}.id"), nullable=False)
    dimension_id = Column(
        Integer, ForeignKey(f"{COSERIES_DIMENSIONS_TABLE}.id"), nullable=False
    )
    analysis_datetime = Column(DateTime, nullable=False)
    score_value = Column(Float, nullable=False)
    spearman_value = Column(Float, nullable=False)
    dtw_value = Column(Float, nullable=False)
    kullback_liebler_value = Column(Float, nullable=False)


# TODO: Move this to muttlib
class View(ABC):

    __schema__ = ""

    @property
    @classmethod
    @abstractmethod
    def __viewname__(cls):
        """Name of the view."""
        raise NotImplementedError("Subclass should implement this.")

    @classproperty
    def viewname(cls):  # pylint:disable=E0213
        """Convenience getter that adds schema if provided."""
        rv = cls.__viewname__
        if cls.__schema__:
            rv = f"{cls.__schema__}.{rv}"
        return rv

    @property
    def columns(self):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_create_sql(cls, engine_name=None):
        """Generate SQL to create the view."""
        raise NotImplementedError("Subclass should implement this.")

    @classmethod
    def get_drop_sql(cls):
        """Generate SQL to drop the view."""
        sql = f"DROP VIEW {cls.viewname}"
        return sql

    @classmethod
    def create(cls, con, checkfirst=True):
        engine = con.engine
        # Only proceed if no view exists or checkfirst is False
        if checkfirst and engine.dialect.has_table(engine, cls.__viewname__):
            logger.info(
                f"Will skip creating {cls.__viewname__} as it already exists and checkfirst is enforced."
            )
            return
        # Fix booleans for Oracle
        sql = cls.get_create_sql(engine.name)
        rv = con.execute(sql)
        return rv

    def drop(self, con):
        """Drop view."""
        sql = self.get_drop_sql()
        rv = con.execute(sql)
        return rv


class Timeline(View):

    __viewname__ = TIMELINE_TABLE
    columns = [
        "forecast_confs.delver_run_id",
        "forecast_confs.factor_conf_id",
        "forecast_confs.forecaster_value_id",
        "forecast_confs.forecast_date",
        "influencer_ids.influencer_run_id",
    ]

    @classmethod
    def get_create_sql(cls, engine_name=None):
        true_bool = 1 if engine_name == "oracle" else True
        select_expr = ",\n".join(cls.columns)
        sql = f"""
    CREATE OR REPLACE VIEW {cls.viewname} AS
        WITH fv_sel AS (
        SELECT
            dr.id AS delver_run_id,
            dr.kpi_id AS kpi_id,
            dr.time_granularity AS time_granularity,
            dr.end_date AS end_date,
            drfc.id AS drfc_id,
            drfc.factor_conf AS factor_conf,
            fv.id AS fv_id,
            fv.forecast_date AS forecast_date
        FROM {ForecasterValues.__tablename__} fv
        JOIN {ForecasterRuns.__tablename__} fr
            ON fv.run_id = fr.id
        JOIN {DelverRunFactorConf.__tablename__} drfc
            ON drfc.forecaster_run_id = fr.id
        JOIN {DelverRunModel.__tablename__} dr ON
            dr.id = drfc.delver_run_id AND
            dr.is_promoted = {true_bool}
        ),

        forecast_confs AS (
        SELECT
            fv_sel.delver_run_id AS delver_run_id,
            fv_sel.drfc_id AS factor_conf_id,
            fv_sel.kpi_id,
            fv_sel.time_granularity,
            fv_sel.factor_conf,
            fv_sel.forecast_date AS forecast_date,
            fv_sel.fv_id AS forecaster_value_id
            FROM fv_sel
            -- For each forecast_date we only keep the one generated in the latest run
            JOIN (
            SELECT max(end_date) AS end_date,
                    kpi_id,
                    time_granularity,
                    factor_conf,
                    forecast_date
            FROM fv_sel
            GROUP BY
                kpi_id, time_granularity, factor_conf, forecast_date
            ) sq ON
                fv_sel.end_date = sq.end_date AND
                fv_sel.kpi_id = sq.kpi_id AND
                fv_sel.time_granularity = sq.time_granularity AND
                fv_sel.factor_conf = sq.factor_conf AND
                fv_sel.forecast_date = sq.forecast_date
        ),

        iv_sel AS (
        SELECT
            dr.kpi_id AS kpi_id,
            dr.time_granularity AS time_granularity,
            drfc.factor_conf AS factor_conf,
            iv.run_id AS influencer_run_id,
            iv.analysis_date
        FROM {InfluencerValues.__tablename__} iv
        JOIN {DelverRunFactorConf.__tablename__} drfc
            ON iv.run_id = drfc.influencer_run_id
        JOIN {DelverRunModel.__tablename__} dr ON
            dr.id = drfc.delver_run_id
        ),

        influencer_ids AS (
        SELECT
            -- For each analysis_date we only keep the one generated in the latest run
            -- (and hence with the maximum influencer_id)
            kpi_id,
            time_granularity,
            factor_conf,
            analysis_date,
            max(influencer_run_id) AS influencer_run_id
        FROM iv_sel
        GROUP BY
            kpi_id, time_granularity, factor_conf, analysis_date
        )

        SELECT {select_expr}
        FROM forecast_confs
        LEFT JOIN influencer_ids ON
            forecast_confs.kpi_id = influencer_ids.kpi_id AND
            forecast_confs.time_granularity = influencer_ids.time_granularity AND
            forecast_confs.factor_conf = influencer_ids.factor_conf AND
            forecast_confs.forecast_date = influencer_ids.analysis_date
        ORDER BY forecaster_value_id, forecast_date
        """
        return sql
