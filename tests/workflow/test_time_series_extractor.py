"""Tests for TimeSeriesExtractor.
"""
import os
import unittest
from unittest import main

import pandas as pd
from sqlalchemy import Column
from sqlalchemy.types import Float, Integer, String

from soam.constants import TIMESTAMP_COL
from soam.data_models import AbstractIDBase, AbstractTimeSeriesTable
from soam.workflow import TimeSeriesExtractor
from tests.db_test_case import TEST_DB_CONNSTR, PgTestCase


class ConcreteTimeSeriesTable(AbstractTimeSeriesTable):
    """Creates the Concrete Time Series Table Object."""

    __tablename__ = "test_data"

    # We should really be using the timestamp inherited from AbstractTimeSeriesTable.

    game = Column(String(64))
    country = Column(String(2))
    ad_network = Column(String(64))
    ad_type = Column(String(64))
    placement_id = Column(String(256))
    waterfall_position = Column(Integer())

    total_count_view_opportunity = Column(Integer())
    count_cache_request = Column(Integer())
    count_cache_success = Column(Integer())
    count_view_start = Column(Integer())
    count_view_click = Column(Integer())
    requests = Column(Integer())
    impressions = Column(Integer())
    clicks = Column(Integer())
    revenue = Column(Float())

    # TODO: Add unique constraint for consistency sake.
    #       https://gitlab.com/mutt_data/tfg-adsplash/-/blob/master/adsplash/store/dataset.py#L442


class ConcreteAdNetworkJoinTimeSeriesTable(AbstractIDBase):
    """Creates the Concrete Ad Network Object."""

    __tablename__ = "test_ad_network_join_data"

    ad_network = Column(String(64))
    ad_network_group = Column(String(64))


class ConcretePlacementIdJoinTimeSeriesTable(AbstractIDBase):
    """Creates the Concrete Placement Id Object."""

    __tablename__ = "test_placement_id_join_data"

    placement_id = Column(String(256))
    placement_id_group = Column(String(64))


column_mappings = {
    "opportunities": "total_count_view_opportunity AS opportunities",
    "ecpm": """COALESCE(
        1000.0 * revenue::float8 / NULLIF(impressions, 0), 0) AS ecpm""",
    "share": """COALESCE(
        impressions::float8
        / NULLIF(total_count_view_opportunity, 0), 0) AS share""",
    "quantile": """
        COALESCE(1 - (
        SUM(impressions)
        OVER (
            PARTITION BY %(quantile_partition)s
            ORDER BY
            timestamp,
            waterfall_position,
            revenue / NULLIF(impressions, 0)
            DESC
            ROWS BETWEEN unbounded preceding AND current row)
        )::float8 / NULLIF(total_count_view_opportunity, 0), 0) AS quantile
        """,
}
aggregated_column_mappings = {
    "opportunities": """
        MAX(total_count_view_opportunity)::float8
        AS opportunities
        """,
    "total_count_view_opportunity": """
        MAX(total_count_view_opportunity)::float8
        AS total_count_view_opportunity
        """,
    "count_cache_request": """
        SUM(count_cache_request) AS count_cache_request
        """,
    "count_cache_success": """
        SUM(count_cache_success) AS count_cache_success
        """,
    "count_view_start": "SUM(count_view_start) AS count_view_start",
    "count_view_click": "SUM(count_view_click) AS count_view_click",
    "requests": "SUM(requests) AS requests",
    "impressions": "SUM(impressions) AS impressions",
    "clicks": "SUM(clicks) AS clicks",
    "revenue": "SUM(revenue) AS revenue",
    "ecpm": """COALESCE(
        1000.0 * SUM(revenue)::float8
        / NULLIF(SUM(impressions), 0), 0) AS ecpm""",
    "share": """COALESCE(
        SUM(impressions)::float8
        / NULLIF(MAX(total_count_view_opportunity), 0), 0) AS share""",
    "quantile": """
        COALESCE(1 - (
            SUM(SUM(impressions))
            OVER (
            PARTITION BY %(quantile_partition)s
            ORDER BY
                timestamp,
                waterfall_position,
                SUM(revenue) / NULLIF(SUM(impressions), 0) DESC
            ROWS BETWEEN unbounded preceding AND current row)
            )::float8 / NULLIF(MAX(total_count_view_opportunity), 0)::float8,
        0) AS quantile
        """,
}


@unittest.skipIf(not os.getenv(TEST_DB_CONNSTR), f"{TEST_DB_CONNSTR} is not set")
class TestDatasetStore(PgTestCase):
    """Test dataset store object."""

    def _test_load(
        self,
        columns,
        dimensions,
        dimensions_values,
        start_date,
        end_date,
        order_by,
        expected_values,
        extra_where_conditions=None,
        extra_having_conditions=None,
        inner_join=None,
        table_mapping=None,
    ):
        df = self.time_series_extractor.extract(
            build_query_kwargs=dict(
                columns=columns,
                dimensions=dimensions,
                dimensions_values=dimensions_values,
                start_date=start_date,
                end_date=end_date,
                order_by=order_by,
                extra_where_conditions=extra_where_conditions,
                extra_having_conditions=extra_having_conditions,
                column_mappings=column_mappings,
                aggregated_column_mappings=aggregated_column_mappings,
                inner_join=inner_join,
                table_mapping=table_mapping,
            )
        )
        # Fix for backwards compatible with original tests.
        if TIMESTAMP_COL in df.columns and not df.empty:
            df[TIMESTAMP_COL] = df[TIMESTAMP_COL].dt.strftime("%Y-%m-%d")
        self.assertTrue(isinstance(df, pd.DataFrame))
        columns = [c_name.split(".")[-1] for c_name in columns]
        self.assertEqual(df.columns.tolist(), columns)
        self.assertEqual(sorted(df.values.tolist()), sorted(expected_values))

    def test_load_basic_columns_order_by(self):
        columns = [TIMESTAMP_COL, "opportunities", "impressions", "revenue"]
        values = [
            ["2019-09-01", 1000, 100, 20],
            ["2019-09-01", 1000, 200, 30],
            ["2019-09-01", 1000, 300, 40],
            ["2019-09-02", 300, 30, 6],
        ]
        self._test_load(
            columns=columns,
            dimensions=None,
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=[TIMESTAMP_COL, "impressions"],
            expected_values=values,
        )

    def test_join_load_basic_columns_order_by(self):
        columns = [TIMESTAMP_COL, "opportunities", "tjd.ad_network", "ad_network_group"]
        values = [
            ['2019-09-01', 1000, 'source1', 'source_group_B'],
            ['2019-09-01', 1000, 'source2', 'source_group_A'],
            ['2019-09-01', 1000, 'source2', 'source_group_A'],
            ['2019-09-02', 300, 'source2', 'source_group_A'],
        ]
        self._test_load(
            columns=columns,
            dimensions=None,
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=[TIMESTAMP_COL, "tjd.ad_network"],
            expected_values=values,
            inner_join=[
                (
                    "test_ad_network_join_data",
                    "tjd",
                    "tjd.ad_network = test_data.ad_network",
                )
            ],
        )

    def test_join_load_basic_columns_order_by_no_alias(self):
        columns = [
            TIMESTAMP_COL,
            "opportunities",
            "test_ad_network_join_data.ad_network",
            "ad_network_group",
        ]
        values = [
            ['2019-09-01', 1000, 'source1', 'source_group_B'],
            ['2019-09-01', 1000, 'source2', 'source_group_A'],
            ['2019-09-01', 1000, 'source2', 'source_group_A'],
            ['2019-09-02', 300, 'source2', 'source_group_A'],
        ]
        self._test_load(
            columns=columns,
            dimensions=None,
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=[TIMESTAMP_COL, "test_ad_network_join_data.ad_network"],
            expected_values=values,
            inner_join=[
                (
                    "test_ad_network_join_data",
                    None,
                    "test_ad_network_join_data.ad_network = test_data.ad_network",
                )
            ],
        )

    def test_join_tables_with_alias(self):
        columns = [
            TIMESTAMP_COL,
            "opportunities",
            "b.ad_network",
            "ad_network_group",
        ]
        values = [
            ['2019-09-01', 1000, 'source1', 'source_group_B'],
            ['2019-09-01', 1000, 'source2', 'source_group_A'],
            ['2019-09-01', 1000, 'source2', 'source_group_A'],
            ['2019-09-02', 300, 'source2', 'source_group_A'],
        ]
        self._test_load(
            columns=columns,
            dimensions=None,
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=None,
            expected_values=values,
            table_mapping='a',
            inner_join=[
                ("test_ad_network_join_data", 'b', "b.ad_network = a.ad_network",)
            ],
        )

    def test_multiple_join_load_basic_columns_order_by(self):
        columns = [
            TIMESTAMP_COL,
            "opportunities",
            "tjd.ad_network",
            "ad_network_group",
            "tpi.placement_id",
            "placement_id_group",
        ]
        values = [
            ['2019-09-01', 1000, 'source1', 'source_group_B', 'z', 'placement_group_1'],
            ['2019-09-01', 1000, 'source2', 'source_group_A', 'b', 'placement_group_2'],
            ['2019-09-01', 1000, 'source2', 'source_group_A', 'a', 'placement_group_1'],
            ['2019-09-02', 300, 'source2', 'source_group_A', 'a', 'placement_group_1'],
        ]
        self._test_load(
            columns=columns,
            dimensions=None,
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=[TIMESTAMP_COL, "tjd.ad_network"],
            expected_values=values,
            inner_join=[
                (
                    "test_ad_network_join_data",
                    "tjd",
                    "tjd.ad_network = test_data.ad_network",
                ),
                (
                    "test_placement_id_join_data",
                    "tpi",
                    "tpi.placement_id = test_data.placement_id",
                ),
            ],
        )

    def test_join_aggregation_load_basic_columns_no_alias(self):
        columns = ["opportunities", "ad_network_group"]
        values = [[1000.0, 'source_group_A'], [1000.0, 'source_group_B']]
        self._test_load(
            columns=columns,
            dimensions=["ad_network_group"],
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=None,
            expected_values=values,
            inner_join=[
                (
                    "test_ad_network_join_data",
                    None,
                    "test_ad_network_join_data.ad_network = test_data.ad_network",
                )
            ],
        )

    def test_multiple_join_aggregation_basic_columns_order_by(self):
        columns = [
            "opportunities",
            "ad_network_group",
            "placement_id_group",
        ]
        values = [
            [1000.0, 'source_group_B', 'placement_group_1'],
            [1000.0, 'source_group_A', 'placement_group_1'],
            [1000.0, 'source_group_A', 'placement_group_2'],
        ]
        self._test_load(
            columns=columns,
            dimensions=["ad_network_group", "placement_id_group"],
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=None,
            expected_values=values,
            inner_join=[
                (
                    "test_ad_network_join_data",
                    "tjd",
                    "tjd.ad_network = test_data.ad_network",
                ),
                (
                    "test_placement_id_join_data",
                    "tpi",
                    "tpi.placement_id = test_data.placement_id",
                ),
            ],
        )

    def test_multiple_join_aggregation_basic_columns_filtered(self):
        columns = [
            "opportunities",
            "ad_network_group",
            "placement_id_group",
        ]
        values = [
            [1000.0, 'source_group_A', 'placement_group_1'],
            [1000.0, 'source_group_A', 'placement_group_2'],
        ]
        self._test_load(
            columns=columns,
            dimensions=["ad_network_group", "placement_id_group"],
            dimensions_values=['source_group_A', None],
            start_date=None,
            end_date=None,
            order_by=None,
            expected_values=values,
            inner_join=[
                (
                    "test_ad_network_join_data",
                    "tjd",
                    "tjd.ad_network = test_data.ad_network",
                ),
                (
                    "test_placement_id_join_data",
                    "tpi",
                    "tpi.placement_id = test_data.placement_id",
                ),
            ],
        )

    def test_load_basic_columns_aggregation_order_by(self):
        columns = ["opportunities", "impressions", "revenue"]
        values = [
            [1000, 600, 90],
            [300, 30, 6],
        ]
        self._test_load(
            columns=columns,
            dimensions=[TIMESTAMP_COL],
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=[TIMESTAMP_COL],
            expected_values=values,
        )

    # def test_load_composite_columns(self):
    #     columns = [TIMESTAMP_COL, "ecpm", "share", "quantile"]
    #     values = [
    #         ["2019-09-01", 1e3 * 40 / 300, 300 / 1000, 0.40],
    #         ["2019-09-01", 1e3 * 30 / 200, 200 / 1000, 0.70],
    #         ["2019-09-01", 1e3 * 20 / 100, 100 / 1000, 0.90],
    #         ["2019-09-02", 1e3 * 6 / 30, 30 / 300, 0.90],
    #     ]
    #     self._test_load(
    #         columns=columns,
    #         dimensions=None,
    #         dimensions_values=None,
    #         start_date=None,
    #         end_date=None,
    #         order_by=[TIMESTAMP_COL, "ecpm"],
    #         expected_values=values,
    #     )

    # def test_load_composite_columns_aggregation(self):
    #     columns = [TIMESTAMP_COL, "waterfall_position", "ecpm", "share", "quantile"]
    #     values = [
    #         ["2019-09-01", 0, 1e3 * 20 / 100, 100 / 1000, 0.90],
    #         ["2019-09-01", 1, 1e3 * 30 / 200, 200 / 1000, 0.70],
    #         ["2019-09-01", 2, 1e3 * 40 / 300, 300 / 1000, 0.40],
    #         ["2019-09-02", 0, 1e3 * 6 / 30, 30 / 300, 0.90],
    #     ]
    #     self._test_load(
    #         columns=columns,
    #         dimensions=[TIMESTAMP_COL, "waterfall_position"],
    #         dimensions_values=None,
    #         start_date=None,
    #         end_date=None,
    #         order_by=[TIMESTAMP_COL, "waterfall_position"],
    #         expected_values=values,
    #     )

    def test_load_all_columns_aggregation(self):
        columns = [
            TIMESTAMP_COL,
            "game",
            "country",
            "ad_network",
            "ad_type",
            "placement_id",
            "waterfall_position",
            "opportunities",
            "count_cache_request",
            "count_cache_success",
            "count_view_start",
            "count_view_click",
            "requests",
            "impressions",
            "clicks",
            "revenue",
        ]
        dimensions = columns[:7]
        values = [
            [
                "2019-09-01",
                "1",
                "us",
                "source1",
                "video",
                "z",
                2,
                1000.0,
                500,
                310,
                300,
                40,
                500,
                300,
                20,
                40.0,
            ],
            [
                "2019-09-01",
                "1",
                "us",
                "source2",
                "media",
                "b",
                1,
                1000.0,
                200,
                41,
                30,
                3,
                200,
                200,
                40,
                30.0,
            ],
            [
                "2019-09-01",
                "1",
                "us",
                "source2",
                "video",
                "a",
                0,
                1000.0,
                150,
                104,
                100,
                20,
                150,
                100,
                10,
                20.0,
            ],
            [
                "2019-09-02",
                "1",
                "us",
                "source2",
                "video",
                "a",
                0,
                300.0,
                300,
                200,
                34,
                1,
                300,
                30,
                1,
                6.0,
            ],
        ]
        self._test_load(
            columns=columns,
            dimensions=dimensions,
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=dimensions,
            expected_values=values,
        )

    def test_load_from_start_date(self):
        columns = [TIMESTAMP_COL, "opportunities", "impressions", "revenue"]
        values = [
            ["2019-09-02", 300, 30, 6],
        ]
        self._test_load(
            columns=columns,
            dimensions=None,
            dimensions_values=None,
            start_date="2019-09-02",
            end_date=None,
            order_by=[TIMESTAMP_COL, "impressions"],
            expected_values=values,
        )

    def test_load_until_end_date(self):
        columns = [TIMESTAMP_COL, "opportunities", "impressions", "revenue"]
        values = [
            ["2019-09-01", 1000, 100, 20],
            ["2019-09-01", 1000, 200, 30],
            ["2019-09-01", 1000, 300, 40],
        ]
        self._test_load(
            columns=columns,
            dimensions=None,
            dimensions_values=None,
            start_date=None,
            end_date="2019-09-01",
            order_by=[TIMESTAMP_COL, "impressions"],
            expected_values=values,
        )

    def test_load_date_range(self):
        columns = [TIMESTAMP_COL, "opportunities", "impressions", "revenue"]
        values = [
            ["2019-09-01", 1000, 100, 20],
            ["2019-09-01", 1000, 200, 30],
            ["2019-09-01", 1000, 300, 40],
        ]
        self._test_load(
            columns=columns,
            dimensions=None,
            dimensions_values=None,
            start_date="2019-09-01",
            end_date="2019-09-01",
            order_by=[TIMESTAMP_COL, "impressions"],
            expected_values=values,
        )

    def test_load_empty(self):
        columns = [TIMESTAMP_COL, "opportunities", "impressions", "revenue"]
        values = []
        self._test_load(
            columns=columns,
            dimensions=None,
            dimensions_values=None,
            start_date="2019-09-03",
            end_date="2019-09-04",
            order_by=[TIMESTAMP_COL, "impressions"],
            expected_values=values,
        )

    def test_load_dimensions_basic_columns(self):
        columns = [TIMESTAMP_COL, "ad_network", "opportunities", "impressions"]
        values = [
            ["2019-09-01", "source1", 1000, 300],
            ["2019-09-01", "source2", 1000, 300],
            ["2019-09-02", "source2", 300, 30],
        ]
        self._test_load(
            columns=columns,
            dimensions=[TIMESTAMP_COL, "ad_network"],
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=[TIMESTAMP_COL, "ad_network"],
            expected_values=values,
        )

    def test_load_dimensions_values(self):
        columns = [TIMESTAMP_COL, "ad_network", "opportunities", "impressions"]
        values = [
            ["2019-09-01", "source2", 1000, 100],
            ["2019-09-01", "source2", 1000, 200],
            ["2019-09-02", "source2", 300, 30],
        ]
        self._test_load(
            columns=columns,
            dimensions=[TIMESTAMP_COL, "ad_network", "waterfall_position"],
            dimensions_values=[None, "source2", None],
            start_date=None,
            end_date=None,
            order_by=[TIMESTAMP_COL, "impressions"],
            expected_values=values,
        )

    def test_load_multiple_dimensions_values(self):
        columns = [TIMESTAMP_COL, "ad_network", "opportunities", "impressions"]
        values = [
            ["2019-09-01", "source1", 1000, 300],
            ["2019-09-01", "source2", 1000, 100],
            ["2019-09-01", "source2", 1000, 200],
            ["2019-09-02", "source2", 300, 30],
        ]
        self._test_load(
            columns=columns,
            dimensions=[TIMESTAMP_COL, "ad_network", "waterfall_position"],
            dimensions_values=[None, ["source1", "source2"], None],
            start_date=None,
            end_date=None,
            order_by=[TIMESTAMP_COL, "ad_network", "impressions"],
            expected_values=values,
        )

    def test_load_multiple_dimensions_values_with_negation(self):
        columns = [TIMESTAMP_COL, "ad_network", "opportunities", "impressions"]
        values = [
            ["2019-09-01", "source1", 1000, 300],
        ]
        self._test_load(
            columns=columns,
            dimensions=[TIMESTAMP_COL, "ad_network", "!ad_type", "!placement_id"],
            dimensions_values=[None, None, "media", ["a", "x"]],
            start_date=None,
            end_date=None,
            order_by=[TIMESTAMP_COL, "ad_network", "impressions"],
            expected_values=values,
        )

    def test_dimension_values(self):
        ret = self.time_series_extractor.dimensions_values(
            dimensions=["ad_network"],
            dimensions_values=None,
            start_date=None,
            end_date=None,
            order_by=["ad_network"],
        )
        self.assertEqual(ret, [["source1"], ["source2"]])

    def test_dimension_values_filtered(self):
        ret = self.time_series_extractor.dimensions_values(
            dimensions=["ad_network", "waterfall_position"],
            dimensions_values=["source2", None],
            start_date=None,
            end_date=None,
            order_by=["ad_network", "waterfall_position"],
        )
        expected = [
            ["source2", 0],
            ["source2", 1],
        ]
        self.assertEqual(ret, expected)

    def test_dimension_values_multiple_dimensions(self):
        ret = self.time_series_extractor.dimensions_values(
            dimensions=["ad_network", "ad_type"],
            dimensions_values=["*", ["video"]],
            start_date=None,
            end_date=None,
            order_by=["ad_network"],
        )
        expected = [
            ["source1", "video"],
            ["source2", "video"],
        ]
        self.assertEqual(ret, expected)

    def test_builded_query_prequery(self):
        columns = [
            "timestamp",
            "game",
            "country",
            "ad_network",
            "ad_type",
            "placement_id",
        ]
        prequery = "SET extra_float_digits = 3;"
        order_by = ["ad_type"]
        start_date = "2019-09-01"
        end_date = "2019-09-02"

        query = self.time_series_extractor.build_query(
            columns=columns,
            prequery=prequery,
            start_date=start_date,
            end_date=end_date,
            order_by=order_by,
        )
        # remove empty spaces and new lines
        returned_query = " ".join(query[0].split())
        return_query = "SET extra_float_digits = 3; SELECT timestamp, game, country, ad_network, ad_type, placement_id FROM test_data WHERE timestamp >= '2019-09-01' AND timestamp <= '2019-09-02' ORDER BY ad_type"
        self.assertEqual(returned_query, return_query)

    def test_builded_query_extra_cond(self):
        columns = [
            "timestamp",
            "game",
            "country",
            "ad_network",
            "ad_type",
            "placement_id",
        ]
        order_by = ["ad_type"]
        start_date = "2019-09-01"
        end_date = "2019-09-02"
        extra_where_conditions = ["game LIKE '%mario%'"]

        query = self.time_series_extractor.build_query(
            columns=columns,
            start_date=start_date,
            end_date=end_date,
            order_by=order_by,
            extra_where_conditions=extra_where_conditions,
        )
        # remove empty spaces and new lines
        returned_query = " ".join(query[0].split())
        return_query = "SELECT timestamp, game, country, ad_network, ad_type, placement_id FROM test_data WHERE timestamp >= '2019-09-01' AND timestamp <= '2019-09-02' AND game LIKE '%mario%' ORDER BY ad_type"
        self.assertEqual(returned_query, return_query)

    @classmethod
    def setUpClass(cls):
        super().setUp(cls)
        cls.time_series_extractor = TimeSeriesExtractor(
            cls.db_client, ConcreteTimeSeriesTable.__tablename__
        )
        engine = cls.db_client.get_engine()
        ConcreteTimeSeriesTable.__table__.create(engine)  # pylint:disable=no-member
        ConcreteAdNetworkJoinTimeSeriesTable.__table__.create(  # pylint:disable=no-member
            engine
        )
        ConcretePlacementIdJoinTimeSeriesTable.__table__.create(  # pylint:disable=no-member
            engine
        )
        query = """
         INSERT INTO test_data
           (timestamp,
            game,
            country,
            ad_network,
            ad_type,
            placement_id,
            waterfall_position,
            total_count_view_opportunity,
            count_cache_request,
            count_cache_success,
            count_view_start,
            count_view_click,
            requests,
            impressions,
            clicks,
            revenue
            )
         VALUES
           ('2019-09-01',
            '1',
            'us',
            'source1',
            'video',
            'z',
            2,
            1000,
            500,
            310,
            300,
            40,
            500,
            300,
            20,
            40
            ),
           ('2019-09-01',
            '1',
            'us',
            'source2',
            'video',
            'a',
            0,
            1000,
            150,
            104,
            100,
            20,
            150,
            100,
            10,
            20
            ),
           ('2019-09-01',
            '1',
            'us',
            'source2',
            'media',
            'b',
            1,
            1000,
            200,
            41,
            30,
            3,
            200,
            200,
            40,
            30
            ),
           ('2019-09-02',
            '1',
            'us',
            'source2',
            'video',
            'a',
            0,
            300,
            300,
            200,
            34,
            1,
            300,
            30,
            1,
            6
            )
        """
        cls.run_query(query)

        query = """
         INSERT INTO test_ad_network_join_data
           (ad_network,
            ad_network_group
            )
         VALUES
           ('source2',
            'source_group_A'
            ),
           ('source1',
            'source_group_B'
            ),
           ('source3',
            'source_group_B'
            )
        """
        cls.run_query(query)

        query = """
         INSERT INTO test_placement_id_join_data
           (placement_id,
            placement_id_group
            )
         VALUES
           ('z',
            'placement_group_1'
            ),
           ('a',
            'placement_group_1'
            ),
           ('b',
            'placement_group_2'
            )
        """
        cls.run_query(query)

    @classmethod
    def tearDownClass(cls):
        # del cls.dataset
        super().tearDown(cls)

    def setUp(self):
        pass

    def tearDown(self):
        pass


if __name__ == "__main__":
    main()
