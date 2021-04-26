"""Test the utils."""
import os
from os import listdir
from pathlib import Path
from typing import List, Tuple
import unittest

import numpy as np
import pandas as pd
import pytest

from soam.utilities.utils import add_future_dates, split_backtesting_ranges

ROOT_TEST_DIRECTORY = Path(__file__).parent / "resources" / "test_utils"
VALIDATION_PREFIX = "validation_"
TRAIN_PREFIX = "train_"


class TestSplitBacktestingRanges(unittest.TestCase):
    """Create an object to test the utils."""

    def setUp(self):
        with open(ROOT_TEST_DIRECTORY / "initial_dataframe.csv") as df_stream:
            self.initial_df = pd.read_csv(df_stream, index_col=0)
        self.initial_df_size = len(self.initial_df)

    def test_empty_dataframe(self):
        # TODO: find how to modify default error message.
        with self.assertRaises(IndexError):
            split_backtesting_ranges(pd.DataFrame())

    def test_test_window_under_minimum_border(self):
        with self.assertRaises(IndexError):
            split_backtesting_ranges(self.initial_df, test_window=0)

    def test_test_window_over_maximum_border(self):
        with self.assertRaises(IndexError):
            split_backtesting_ranges(self.initial_df, test_window=self.initial_df_size)

    def test_train_window_under_minimum_border(self):
        with self.assertRaises(IndexError):
            split_backtesting_ranges(self.initial_df, train_window=0)

    def test_train_window_over_maximum_border(self):
        with self.assertRaises(IndexError):
            split_backtesting_ranges(self.initial_df, train_window=self.initial_df_size)

    def test_step_size_under_minimum_border(self):
        with self.assertRaises(IndexError):
            split_backtesting_ranges(self.initial_df, step_size=0)

    def test_all_default(self):
        self.template_test_against_initial_df(
            "all_default/", "default parameters failing"
        )

    def test_test_window_maximum_border(self):
        self.template_test_against_initial_df(
            "test_window_maximum_border/",
            "maximum test window value failing",
            test_window=self.initial_df_size - 1,
        )

    def test_train_window_maximum_border(self):
        self.template_test_against_initial_df(
            "train_window_maximum_border/",
            "maximum train window value failing",
            train_window=self.initial_df_size - 1,
        )

    def test_step_size_equal_to_df_len(self):
        self.template_test_against_initial_df(
            "step_size_equal_to_df_size/",
            "df len step size value failing",
            step_size=self.initial_df_size,
        )

    def test_normal_usage_sliding(self):
        self.template_test_against_initial_df(
            "test_normal_usage_sliding/",
            "normal usage with sliding window" " failing",
            test_window=2,
            train_window=2,
            step_size=2,
        )

    def test_normal_usage_expanding(self):
        self.template_test_against_initial_df(
            "test_normal_usage_expanding/",
            "normal usage with expanding window" " failing",
            test_window=2,
            train_window=None,
            step_size=2,
        )

    def template_test_against_initial_df(
        self, folder: Path, error_message: str, **split_backtesting_ranges_kwarg
    ):
        """
        Test the result of passing the initial dataframe to split_backtesting_ranges,
        using split_backtesting_ranges_kwarg, against the dataframes contained in
        folder.

        Parameters
        ----------
        folder: pathlib.Path
            Path to the directory to drawn train and validation dataframes.
        error_message: str
            Path to the directory to drawn train and validation dataframes.
        split_backtesting_ranges_kwarg: dict
            The keyword arguments for split_backtesting_ranges.

        See Also
        --------
        load_directory_dataframes : to know the file naming convention to load the train
         and validation datasets.
        """
        output = split_backtesting_ranges(
            self.initial_df, **split_backtesting_ranges_kwarg
        )
        expected_output = self.load_directory_dataframes(ROOT_TEST_DIRECTORY / folder)
        self.assertEqual(len(expected_output), len(output), error_message)
        for (
            [train_df_function, test_df_function],
            [train_df_loaded, test_df_loaded],
        ) in zip(output, expected_output):
            self.assertTrue(train_df_function.equals(train_df_loaded), error_message)
            self.assertTrue(test_df_function.equals(test_df_loaded), error_message)

    @staticmethod
    def load_directory_dataframes(
        path: Path,
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Loads splitted train-validation dataframes from a directory.

        The pair of csvs in the directory named "{TRAIN_PREFIX}{step}.csv" and
        "{VALIDATION_PREFIX}{step}.csv" would be loaded as a list of tuples of (train,
         validation) dataframes.

         TRAIN_PREFIX and VALIDATION_PREFIX constant are declared at the beginning
         of this file.

        Parameters
        ----------
        path: pathlib.Path
            Path to the directory to drawn train and validation dataframes.

        Returns
        -------
        list of tuple of pd.DataFrame
            The train and validation dataframes loaded from the directory.
        """
        # TODO: move this dataframes in csvs to code.
        directory_dataframes = dict()
        for validation_file_name in listdir(path):
            splited_file_name = os.path.splitext(validation_file_name)
            train_file_name = validation_file_name.replace(
                VALIDATION_PREFIX, TRAIN_PREFIX
            )
            if (
                (path / train_file_name).is_file()
                and len(splited_file_name) == 2
                and VALIDATION_PREFIX in splited_file_name[0]
                and splited_file_name[1] == ".csv"
            ):
                with open(path / train_file_name) as train_stream, open(
                    path / validation_file_name
                ) as validation_stream:
                    directory_dataframes[validation_file_name] = (
                        pd.read_csv(train_stream, index_col=0),
                        pd.read_csv(validation_stream, index_col=0),
                    )
        return [
            directory_dataframes[loaded_split_name]
            for loaded_split_name in sorted(directory_dataframes.keys())
        ]


def test_add_future_dates_frequency_not_inferred():
    """Test that frequency can't be inferred."""
    test_data = pd.DataFrame.from_records(
        np.array(
            [
                ('2016-06-01T00:00:00.000000000', 453990.926731),
                ('2016-07-03T00:00:00.000000000', 461908.605069),
                ('2016-08-04T00:00:00.000000000', 482625.559603),
                ('2016-09-05T00:00:00.000000000', 438345.625953),
                ('2016-10-01T00:00:00.000000000', 458133.301185),
                ('2016-11-01T00:00:00.000000000', 467090.524589),
                ('2016-12-03T00:00:00.000000000', 508706.424433),
                ('2017-12-06T00:00:00.000000000', 426140.823832),
                ('2017-02-08T00:00:00.000000000', 418005.414117),
                ('2017-03-15T00:00:00.000000000', 470489.149374),
            ],
            dtype=[('ds', '<M8[ns]'), ('y', '<f8')],
        )
    )
    with pytest.raises(ValueError):
        add_future_dates(test_data, periods=5)
        add_future_dates(test_data.iloc[:1, :], periods=5)


def test_add_future_dates():
    """Test that future dates are generated as expected."""
    test_data = pd.DataFrame.from_records(
        np.array(
            [
                ('2016-06-01T00:00:00.000000000', 453990.926731),
                ('2016-07-01T00:00:00.000000000', 461908.605069),
                ('2016-08-01T00:00:00.000000000', 482625.559603),
                ('2016-09-01T00:00:00.000000000', 438345.625953),
                ('2016-10-01T00:00:00.000000000', 458133.301185),
                ('2016-11-01T00:00:00.000000000', 467090.524589),
                ('2016-12-01T00:00:00.000000000', 508706.424433),
                ('2017-01-01T00:00:00.000000000', 426140.823832),
                ('2017-02-01T00:00:00.000000000', 418005.414117),
                ('2017-03-01T00:00:00.000000000', 470489.149374),
            ],
            dtype=[('ds', '<M8[ns]'), ('y', '<f8')],
        )
    )
    new_df = add_future_dates(test_data, periods=5)
    future_df = pd.DataFrame.from_records(
        np.array(
            [
                ('2017-04-01T00:00:00.000000000', np.nan),
                ('2017-05-01T00:00:00.000000000', np.nan),
                ('2017-06-01T00:00:00.000000000', np.nan),
                ('2017-07-01T00:00:00.000000000', np.nan),
                ('2017-08-01T00:00:00.000000000', np.nan),
            ],
            dtype=[('ds', '<M8[ns]'), ('y', '<f8')],
        )
    )
    expected_df = pd.concat([test_data, future_df]).reset_index(drop=True)
    pd.testing.assert_frame_equal(expected_df, new_df)


if __name__ == '__main__':
    unittest.main()
