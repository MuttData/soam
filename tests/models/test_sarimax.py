from unittest.mock import MagicMock, patch

import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from soam.constants import DS_COL, YHAT_COL
from soam.models.sarimax import SkSarimax
from soam.utilities.utils import add_future_dates
from tests.helpers import sample_data_df  # pylint: disable=unused-import


def test_fit(sample_data_df):  # pylint: disable=redefined-outer-name
    with patch("soam.models.sarimax.SARIMAX") as model_patch:
        output_length = 10
        train_data = sample_data_df
        data = add_future_dates(train_data, output_length)
        X, y = data[data.columns[:-1]], data[data.columns[-1]]
        wrapper = SkSarimax()
        model_patch.assert_not_called()
        wrapper.fit(X, y)
        model_patch.assert_called_once()
        model_patch().fit.assert_called_once()


def test_predict_without_fit_fails(
    sample_data_df,
):  # pylint: disable=redefined-outer-name
    with patch("soam.models.sarimax.SARIMAX") as model_patch:
        output_length = 10
        train_data = sample_data_df
        data = add_future_dates(train_data, output_length)
        X = data[data.columns[:-1]]
        wrapper = SkSarimax()
        model_patch.assert_not_called()
        with pytest.raises(AttributeError):
            wrapper.predict(X)


def test_fit_transform(sample_data_df,):  # pylint: disable=redefined-outer-name
    with patch("soam.models.sarimax.SARIMAX") as model_patch:
        output_length = 10
        train_data = sample_data_df
        data = add_future_dates(train_data, output_length)
        X, y = data[data.columns[:-1]], data[data.columns[-1]]
        wrapper = SkSarimax()
        model_patch.assert_not_called()
        # Setup mock for fit() return value
        pred_mock = MagicMock()
        prediction_values = pd.Series([i for i in range(output_length)])
        pred_mock.predict.return_value = prediction_values
        model_patch.return_value.fit.return_value = pred_mock
        # Run fit_transform
        predictions = wrapper.fit_transform(X, y, output_length=output_length)
        model_patch.assert_called_once()
        model_patch.return_value.fit.assert_called_once()
        pred_mock.predict.assert_called_once()
        # Setup expected prediction
        expected_predictions = pd.DataFrame(
            {
                DS_COL: X[DS_COL].values[-output_length:],
                YHAT_COL: prediction_values.values,
            }
        )
        assert_frame_equal(predictions, expected_predictions)
