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
    def test_store_df(self, cls):
        df = pd.DataFrame(
            {
                "date": [1, 2, 3],
                "country": ["ARG", "BRZ", "ARG"],
                "metric1": [328, 215, 146],
            }
        )
        self.store.run(df)
        sql_select = f"""
        SELECT * FROM {TABLE_STORE}
        """
        pd.testing.assert_frame_equal(cls.db_client.to_frame(sql_select), df)

    @classmethod
    def setUpClass(cls):
        super().setUp(cls)
        query_create = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_STORE}
            (date INT,
            country VARCHAR (50),
            metric1 INT)
            """
        cls.run_query(query_create)
        cls.store = Store(cls.db_client, f"{cls.db_client.database}.{TABLE_STORE}")

    @classmethod
    def tearDownClass(cls):
        super().tearDown(cls)

    def setUp(self):
        pass

    def tearDown(self):
        pass


if __name__ == "__main__":
    main()
