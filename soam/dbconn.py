# FIXME: Use muttlib
"""Module to get and use multiple Big Data DB connections."""
import logging
import re
import shutil
from contextlib import contextmanager
from functools import wraps
from os import makedirs
from time import sleep
from urllib.parse import urlparse

# import cx_Oracle
import pandas as pd
import progressbar

# import pyarrow.parquet as pq
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# import utils
from utils import path_or_string
from constants import PARENT_LOGGER

"""
if True:
    # We seem to need this order to avoid TCLI import errors
    from pyhive import hive
    import ibis
    import ibis.config as cf
"""

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


def _parse_sql_statement_decorator(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        args = list(args)  # type: ignore
        sql = path_or_string(args[0])
        format_params = kwargs.get("params", None)
        if format_params:
            try:
                sql = sql.format(**format_params)
            except KeyError as e:
                if e not in format_params:
                    # If the sql string has an unformatted key then fail
                    raise
                else:
                    pass

        logger.debug(f"Running the following query: \n{sql}")
        args[0] = sql  # type: ignore
        return func(self, *args, **kwargs)

    return wrapper


class BaseClient:
    """Create BaseClient for DBs."""

    def __init__(
        self,
        username,
        database=None,
        host=None,
        dialect=None,
        port=None,
        driver=None,
        password=None,
    ):
        self.dialect = dialect
        self.host = host
        self.username = username
        self.database = database
        self.port = port
        self.driver = driver
        self.password = password
        self._engine = None

    @property
    def _db_uri(self):
        dialect = (
            f"{self.dialect}{f'+{self.driver}' if self.driver is not None else ''}"
        )
        login = (
            f"{self.username}{f':{self.password}' if self.password is not None else ''}"
        )
        host = f"{self.host}{f':{self.port}' if self.port is not None else ''}"
        return f"{dialect}://{login}@{host}/{self.database}"

    def get_engine(self, custom_uri=None, connect_args=None):
        connect_args = connect_args or {}
        if not self._engine:
            db_uri = custom_uri or self._db_uri
            self._engine = create_engine(db_uri, **connect_args)
        return self._engine

    def _connect(self):
        return self.get_engine().connect()

    @staticmethod
    def _cursor_columns(cursor):
        if hasattr(cursor, "keys"):
            return cursor.keys()
        else:
            return [c[0] for c in cursor.description]

    @_parse_sql_statement_decorator
    def execute(self, sql, params=None, connection=None):  # pylint:disable=W0613
        """Execute sql statement."""
        if connection is None:
            connection = self._connect()
        return connection.execute(sql)

    def to_frame(self, *args, **kwargs):
        """Execute sql statement and return results as a Pandas dataframe."""
        cursor = self.execute(*args, **kwargs)
        if not cursor:
            return
        data = cursor.fetchall()
        if data:
            df = pd.DataFrame(data, columns=self._cursor_columns(cursor))
        else:
            df = pd.DataFrame()
        return df

    def insert_from_frame(self, df, table, if_exists="append", index=False, **kwargs):
        """Insert data from dataframe into sql table."""
        # TODO: Validate types here?
        if self.dialect == "oracle":
            df.columns = [c.upper() for c in df.columns]

        connection = self._connect()
        with connection:
            df.to_sql(table, connection, if_exists=if_exists, index=index, **kwargs)


class PgClient(BaseClient):
    """Create Postgres DB client."""

    def __init__(self, dialect="postgresql", port=5433, **kwargs):
        super().__init__(dialect=dialect, port=port, **kwargs)


class OracleClient(BaseClient):
    """Create Oracle DB client."""

    def __init__(self, dialect="oracle", schema=None, **kwargs):
        super().__init__(dialect=dialect, **kwargs)
        self.schema = schema

    @property
    def _db_uri(self):
        dsn = cx_Oracle.makedsn(self.host, self.port, service_name=self.database)
        db_uri = f"{self.dialect}://{self.username}:{self.password}@{dsn}"
        return db_uri

    def _connect(self):
        conn = self.get_engine().connect()
        if self.schema is not None:
            conn.connection.current_schema = self.schema
        return conn


class IbisClient:
    # [REMOVED]
    pass


class HiveDb:
    # [REMOVED]
    pass


@contextmanager
def session_scope(engine=None, **session_kw):
    """Provide a transactional scope around a series of operations."""

    Session = sessionmaker(bind=engine)
    sess = Session(**session_kw)
    # bring_table_group_metadata(sess.connection())
    try:
        yield sess
        sess.commit()
    except Exception as err:
        logger.exception(err)
        sess.rollback()
        raise
    finally:
        sess.close()


IBIS_DB_TYPE = "ibis"
ORACLE_DB_TYPE = "oracle"
POSTGRES_DB_TYPE = "postgres"
HIVE_DB_TYPE = "hive"
IMPALA_DB_TYPE = "impala"
CONNECTORS = {
    IBIS_DB_TYPE: IbisClient,
    ORACLE_DB_TYPE: OracleClient,
    POSTGRES_DB_TYPE: PgClient,
    HIVE_DB_TYPE: HiveDb,
    IMPALA_DB_TYPE: HiveDb,
}


def get_db_client(creds):
    """Do the same get_client but use OracleClientEx."""
    # TODO: Implement some king of regitration logic for this.
    db_type = creds["db_type"]
    if db_type not in CONNECTORS:
        raise ValueError(f"Bad DB selection: {db_type}")
    connector = CONNECTORS[db_type]
    creds_sel = {k: v for k, v in creds.items() if k != "db_type"}
    return connector(**creds_sel)
