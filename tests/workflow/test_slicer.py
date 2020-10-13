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

    def _test_slices(
        self, dimensions, length, value, check_keys=False, keys_check=None
    ):

        slicer_test = Slicer(dimensions, None)
        dataframes = slicer_test.run(self.df)

        if not check_keys:
            self.assertEqual(len(dataframes), length)
            for dataframe in dataframes.values():
                self.assertTrue(isinstance(dataframe, pd.DataFrame))
                self.assertEqual(dataframe.columns.tolist(), self.columns)

            self.assertEqual(sum(list(dataframes.values())[0].opportunities), value)

        if check_keys:
            self.assertEqual(list(dataframes.keys())[0], keys_check)

    def test_slice_one_column(self):
        self._test_slices(["letter"], 2, 1600)

    def test_slice_two_column(self):
        self._test_slices(["letter", "move"], 4, 1400)

    def test_slice_keys(self):
        self._test_slices(["letter", "move"], 6, 1400, True, ("A", "down"))

    def test_slice_bad_dimension(self):
        with self.assertRaises(ValueError):
            self._test_slices(["letter", "mover"], 0, 0)


if __name__ == "__main__":
    main()
