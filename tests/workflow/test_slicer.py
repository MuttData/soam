from unittest import TestCase, main

import pandas as pd

from soam.workflow import Slicer


class TestSlicer(TestCase):
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

    def _test_slices(self, dimensions, length, value):

        slicer_test = Slicer(
            dimensions=dimensions, metrics="opportunities", ds_col="date"
        )
        dataframes = slicer_test.run(self.df)

        self.assertEqual(len(dataframes), length)
        for dataframe in dataframes:
            self.assertIsInstance(dataframe, pd.DataFrame)
            self.assertIn(
                dataframe.columns.tolist(),
                [
                    ['date', 'letter', 'opportunities'],
                    ['date', 'move', 'opportunities'],
                ],
            )

        self.assertEqual(dataframes[0].opportunities.sum(), value)

    def test_slice_one_column(self):
        self._test_slices("letter", 2, 1600)

    def test_slice_two_column(self):
        self._test_slices(["letter", "move"], 8, 1400)

    def test_slice_bad_dimension(self):
        with self.assertRaises(ValueError):
            self._test_slices(["letter", "mover"], 0, 0)


if __name__ == "__main__":
    main()
