"""Testing the database case."""
import logging
import os
from unittest import TestCase

from muttlib.dbconn import get_client_from_connstr
from sqlalchemy.exc import ResourceClosedError

logger = logging.getLogger(__name__)

TEST_DB_CONNSTR = "TEST_DB_CONNSTR"
TEST_DB_NAME = "pytests"
POSTGRES_DB = "soam_db"


class PgTestCase(TestCase):
    """Creates the Test Case object."""

    db_connstr = os.getenv(TEST_DB_CONNSTR)
    if db_connstr:
        _, db_client = get_client_from_connstr(db_connstr)
        prev_database = db_client.database
        # db_client.database = TEST_DB_NAME
    else:
        logger.warning(f"Missing test database connection string in {TEST_DB_CONNSTR}")

    @classmethod
    def run_query(cls, query):
        cursor = cls.db_client.execute(query)
        try:
            ret = list(cursor)
        except ResourceClosedError:  # no results to fetch
            ret = None
        cursor.close()
        return ret

    def setUp(self):
        # self.db_client.database =  os.getenv(POSTGRES_DB)
        self.db_client._engine = None  # pylint:disable=protected-access
        conn = self.db_client._connect()  # pylint:disable=protected-access
        # DROP/CREATE DATABASE fails in a normal session.
        # Ref: https://stackoverflow.com/questions/44959599/sql-alchemy-cannot-run-inside-a-transaction-block
        query = f"""
        DROP DATABASE IF EXISTS {TEST_DB_NAME};
        """
        conn.execution_options(isolation_level="AUTOCOMMIT").execute(query)
        query = f"""
        CREATE DATABASE {TEST_DB_NAME};
        """
        conn.execution_options(isolation_level="AUTOCOMMIT").execute(query)
        conn.close()
        self.db_client._engine = None  # pylint:disable=protected-access
        # self.db_client.database = TEST_DB_NAME

    def tearDown(self):
        # FIXME: This should drop the test database but it fails. The reason seem to be
        # that seems that one or more connection are leaking during the tests.
        # del self.db_client
        # self.db_client = None
        # db_connstr = os.getenv(TEST_DB_CONNSTR)
        # _, db_client = get_client_from_connstr(self.db_connstr)
        # conn = db_client._connect()
        # query = f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"
        # conn.execution_options(isolation_level="AUTOCOMMIT").execute(query)
        # conn.close()
        pass
