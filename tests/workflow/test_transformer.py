"""Transformer tester."""
from unittest import TestCase

import pandas as pd
from sklearn.preprocessing import StandardScaler

from soam.workflow import BaseDataFrameTransformer, Transformer


class SimpleProcessor(BaseDataFrameTransformer):
    """Creates the Simple Processor Object."""

    def __init__(self, **fit_params):
        self.preproc = StandardScaler(**fit_params)

    def fit(self, df_X):
        """Fit."""
        self.preproc.fit(df_X['a'].values.reshape(-1, 1))
        return self

    def transform(self, df_X, inplace=True):
        """Transform."""
        if not inplace:
            df_X = df_X.copy()
        df_X['a'] = self.preproc.transform(df_X['a'].values.reshape(-1, 1))
        return df_X


class TransformerTestCase(TestCase):
    """Creates the Transformer Test Case Object."""

    def test_simple_case(self):
        """Simple case testing."""
        test_data_X = pd.DataFrame({'a': [1, 2, 3]})
        test_data_X2 = pd.DataFrame({'a': [4, 6, 8]})
        expected_output = pd.DataFrame({"a": [-1.2247448714, 0.0, 1.2247448714]})
        expected_output_2 = pd.DataFrame({"a": [2.449490, 4.898979, 7.348469]})

        preproc = Transformer(SimpleProcessor())
        transformed_dataset, _ = preproc.run(test_data_X)

        pd.testing.assert_frame_equal(transformed_dataset, expected_output)
        pd.testing.assert_frame_equal(
            preproc.transform(test_data_X2), expected_output_2
        )
