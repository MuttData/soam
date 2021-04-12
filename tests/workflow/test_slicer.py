"""Slicer tester."""
from unittest import TestCase, main

import pandas as pd

from soam.workflow import Slicer


class TestSlicer(TestCase):
    """Creates the slicer tester object."""

    columns = ["date", "letter", "move", "opportunities", "impressions", "revenue"]
    values = [
        ["2019-09-01", "A", "down", 1000, 100, 20],
        ["2019-09-01", "B", "down", 500, 68, 30],
        ["2019-09-02", "A", "down", 400, 300, 52],
        ["2019-09-02", "B", "up", 300, 35, 6],
        ["2019-09-03", "A", "up", 200, 10, 40],
        ["2019-09-03", "B", "up", 700, 30, 9],
    ]
    df = pd.DataFrame(data=values, columns=columns)

    def _test_slices(self, dimensions, metrics, length, dfs):

        slicer_test = Slicer(dimensions=dimensions, metrics=metrics, ds_col="date")
        dataframes = slicer_test.run(self.df)

        self.assertEqual(len(dataframes), length)
        for df_returned, df_passed in zip(dataframes, dfs):
            df_returned.reset_index(inplace=True, drop=True)
            df_passed.reset_index(inplace=True, drop=True)
            pd.testing.assert_frame_equal(
                df_returned, df_passed, check_index_type=False, check_like=True
            )

    def test_slice_one_column(self):
        """Tests the slice on one column."""
        columns = ["date", "letter", "opportunities"]
        df1 = pd.DataFrame(
            columns=columns,
            data=[
                ["2019-09-01", "A", 1000],
                ["2019-09-02", "A", 400],
                ["2019-09-03", "A", 200],
            ],
        )
        df2 = pd.DataFrame(
            columns=columns,
            data=[
                ["2019-09-01", "B", 500],
                ["2019-09-02", "B", 300],
                ["2019-09-03", "B", 700],
            ],
        )
        dfs = [df1, df2]
        self._test_slices("letter", "opportunities", 2, dfs)

    def test_slice_two_column(self):
        """Tests the slice on two columns."""
        columns1 = ["date", "letter", "opportunities"]
        columns2 = ["date", "move", "opportunities"]
        df1 = pd.DataFrame(
            columns=columns1,
            data=[
                ["2019-09-01", "A", 1000],
                ["2019-09-02", "A", 400],
                ["2019-09-03", "A", 200],
            ],
        )
        df2 = pd.DataFrame(
            columns=columns1,
            data=[
                ["2019-09-01", "B", 500],
                ["2019-09-02", "B", 300],
                ["2019-09-03", "B", 700],
            ],
        )
        df3 = pd.DataFrame(
            columns=columns2,
            data=[
                ["2019-09-01", "down", 1000],
                ["2019-09-01", "down", 500],
                ["2019-09-02", "down", 400],
            ],
        )
        df4 = pd.DataFrame(
            columns=columns2,
            data=[
                ["2019-09-02", "up", 300],
                ["2019-09-03", "up", 200],
                ["2019-09-03", "up", 700],
            ],
        )
        dfs = [df1, df2, df3, df4]
        self._test_slices(["letter", "move"], "opportunities", 4, dfs)

    def test_slice_two_dimensions(self):
        """Tests the slice on two dimensions."""
        columns = ["date", "letter", "move", "opportunities"]
        df1 = pd.DataFrame(
            columns=columns,
            data=[["2019-09-01", "A", "down", 1000], ["2019-09-02", "A", "down", 400],],
        )

        df2 = pd.DataFrame(columns=columns, data=[["2019-09-03", "A", "up", 200],])
        df3 = pd.DataFrame(columns=columns, data=[["2019-09-01", "B", "down", 500],])
        df4 = pd.DataFrame(
            columns=columns,
            data=[["2019-09-02", "B", "up", 300], ["2019-09-03", "B", "up", 700],],
        )
        dfs = [df1, df2, df3, df4]
        self._test_slices([["letter", "move"]], "opportunities", 4, dfs)

    def test_slice_two_metrics(self):
        """Tests the slice on two metrics."""
        columns1 = ["date", "letter", "opportunities"]
        columns2 = ["date", "letter", "impressions"]
        df1 = pd.DataFrame(
            columns=columns1,
            data=[
                ["2019-09-01", "A", 1000],
                ["2019-09-02", "A", 400],
                ["2019-09-03", "A", 200],
            ],
        )
        df3 = pd.DataFrame(
            columns=columns1,
            data=[
                ["2019-09-01", "B", 500],
                ["2019-09-02", "B", 300],
                ["2019-09-03", "B", 700],
            ],
        )
        df2 = pd.DataFrame(
            columns=columns2,
            data=[
                ["2019-09-01", "A", 100],
                ["2019-09-02", "A", 300],
                ["2019-09-03", "A", 10],
            ],
        )
        df4 = pd.DataFrame(
            columns=columns2,
            data=[
                ["2019-09-01", "B", 68],
                ["2019-09-02", "B", 35],
                ["2019-09-03", "B", 30],
            ],
        )
        dfs = [df1, df2, df3, df4]
        self._test_slices("letter", ["opportunities", "impressions"], 4, dfs)

    def test_slice_bad_dimension(self):
        """Tests the slice on a bad dimension."""
        with self.assertRaises(ValueError):
            self._test_slices("lette", "opportunities", 0, 0)


if __name__ == "__main__":
    main()
