import os
from os import listdir
from os.path import isfile
from typing import List, Tuple
import unittest

import pandas as pd

from soam.utils import split_backtesting_ranges

ROOT_TEST_DIRECTORY = "resources/test_utils/"
VALIDATION_PREFIX = "validation_"
TRAIN_PREFIX = "train_"


class TestSplitBacktestingRanges(unittest.TestCase):
    def setUp(self):
        with open(ROOT_TEST_DIRECTORY + "initial_dataframe.csv") as df_stream:
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
        self, folder: str, error_message: str, **split_backtesting_ranges_kwarg
    ):
        """
        Test the result of passing the initial dataframe to split_backtesting_ranges,
        using split_backtesting_ranges_kwarg, against the dataframes contained in
        folder.

        Parameters
        ----------
        folder: str
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
        expected_output = self.load_directory_dataframes(ROOT_TEST_DIRECTORY + folder)
        self.assertEqual(len(expected_output), len(output), error_message)
        for (
            [train_df_function, test_df_function],
            [train_df_loaded, test_df_loaded],
        ) in zip(output, expected_output):
            self.assertTrue(train_df_function.equals(train_df_loaded), error_message)
            self.assertTrue(test_df_function.equals(test_df_loaded), error_message)

    @staticmethod
    def load_directory_dataframes(path: str) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Loads splitted train-validation dataframes from a directory.

        The pair of csvs in the directory named "{TRAIN_PREFIX}{step}.csv" and
        "{VALIDATION_PREFIX}{step}.csv" would be loaded as a list of tuples of (train,
         validation) dataframes.

         TRAIN_PREFIX and VALIDATION_PREFIX constant are declared at the beginning
         of this file.

        Parameters
        ----------
        path: str
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
                isfile(path + train_file_name)
                and len(splited_file_name) == 2
                and VALIDATION_PREFIX in splited_file_name[0]
                and splited_file_name[1] == ".csv"
            ):
                with open(path + train_file_name) as train_stream, open(
                    path + validation_file_name
                ) as validation_stream:
                    directory_dataframes[validation_file_name] = (
                        pd.read_csv(train_stream, index_col=0),
                        pd.read_csv(validation_stream, index_col=0),
                    )
        return [
            directory_dataframes[loaded_split_name]
            for loaded_split_name in sorted(directory_dataframes.keys())
        ]


if __name__ == '__main__':
    unittest.main()
