"""Tests for TimeSeriesExtractor.
"""
import os
import unittest
from unittest import main

from muttlib.dbconn import get_client_from_connstr
import pandas as pd
from sqlalchemy import Column
from sqlalchemy.types import Integer, String

from soam.data_models import AbstractIDBase
from soam.workflow import Store
from tests.db_test_case import TEST_DB_CONNSTR, PgTestCase

TABLE_STORE = "test_store"


class ConcreteTableStore(AbstractIDBase):
    __tablename__ = TABLE_STORE

    country = Column(String(3))
    metric1 = Column(Integer())


@unittest.skipIf(not os.getenv(TEST_DB_CONNSTR), f"{TEST_DB_CONNSTR} is not set")
class TestStore(PgTestCase):
    def test_store_df(self):
        """Test storing data and retriving it."""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "country": ["ARG", "BRZ", "ARG"],
                "metric1": [328, 215, 146],
            }
        )
        self.store.run(df)
        sql_select = f"""
        SELECT * FROM {TABLE_STORE}
        """
        db_connstr = os.getenv(TEST_DB_CONNSTR)
        _, db_client = get_client_from_connstr(db_connstr)
        pd.testing.assert_frame_equal(db_client.to_frame(sql_select), df)

    @classmethod
    def setUpClass(cls):
        super().setUp(cls)

        db_connstr = os.getenv(TEST_DB_CONNSTR)
        engine = cls.db_client.get_engine(db_connstr)
        ConcreteTableStore.__table__.create(engine)
        cls.store = Store(cls.db_client, f"{TABLE_STORE}")

    @classmethod
    def tearDownClass(cls):
        super().tearDown(cls)
        db_connstr = os.getenv(TEST_DB_CONNSTR)
        engine = cls.db_client.get_engine(db_connstr)
        ConcreteTableStore.__table__.drop(engine)

    def setUp(self):
        pass

    def tearDown(self):
        pass


if __name__ == "__main__":
    main()
