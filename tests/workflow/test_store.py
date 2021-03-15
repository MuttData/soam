"""Tests for TimeSeriesExtractor.
"""
import os
import unittest
from unittest import main

import pandas as pd

from soam.workflow import Store
from tests.db_test_case import TEST_DB_CONNSTR, PgTestCase

TABLE_STORE = "test_store"


@unittest.skipIf(not os.getenv(TEST_DB_CONNSTR), f"{TEST_DB_CONNSTR} is not set")
class TestStore(PgTestCase):
    def test_create(self):
        breakpoint()
        query_create = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_STORE}
            (date INT,
            country VARCHAR (50) ,
            metric1 INT)
            """
        self.run_query(query_create)

        # assert table exist
        query_assert = f"SELECT to_regclass('{self.db_client.database}.{TABLE_STORE}');"
        self.assertTrue(self.run_query(query_assert))

    def store_df(self, mocker):
        df = pd.DataFrame(
            {
                "date": [1, 2, 3],
                "country": ["ARG", "BRZ", "ARG"],
                "metric1": [328, 215, 146],
            }
        )
        spy = mocker.spy(self.db_client.insert_from_frame)
        s = Store(self.db_client, TABLE_STORE, self.db_client.database)
        s.run(df)

        spy.assert_called_once_with(df)

    @classmethod
    def setUpClass(cls):
        super().setUp(cls)

    @classmethod
    def tearDownClass(cls):
        super().tearDown(cls)

    def setUp(self):
        pass

    def tearDown(self):
        pass


if __name__ == "__main__":
    main()
