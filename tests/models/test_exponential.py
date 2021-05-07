from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_series_equal
import pytest  # pylint: disable=import-error

from soam.models import SkExponentialSmoothing
from soam.utilities.utils import add_future_dates
from tests.helpers import sample_data_df  # pylint: disable=unused-import


def test_input_format_exponential(
    sample_data_df,
):  # pylint: disable=redefined-outer-name
    output_length = 10
    train_data = sample_data_df
    data = add_future_dates(train_data, output_length)
    X, y = data[data.columns[:-1]], data[data.columns[-1]]
    wrapper = SkExponentialSmoothing()
    endog = wrapper._transform_to_input_format(X, y)  # pylint: disable=protected-access
    expected_endog = pd.Series(data.y.values, index=data.ds.values)
    assert_series_equal(endog, expected_endog)


def test_predict_without_fit_fails_exponential(
    sample_data_df,
):  # pylint: disable=redefined-outer-name
    with patch("soam.models._exponential.ExponentialSmoothing") as model_patch:
        output_length = 10
        train_data = sample_data_df
        data = add_future_dates(train_data, output_length)
        X = data[data.columns[:-1]]
        wrapper = SkExponentialSmoothing()
        model_patch.assert_not_called()
        with pytest.raises(AttributeError):
            wrapper.predict(X)


def test_fit_transform_exponential(
    sample_data_df,
):  # pylint: disable=redefined-outer-name
    with patch("soam.models._exponential.ExponentialSmoothing") as model_patch:
        output_length = 10
        train_data = sample_data_df
        data = add_future_dates(train_data, output_length)
        X, y = data[data.columns[:-1]], data[data.columns[-1]]
        wrapper = SkExponentialSmoothing()
        wrapper.fit_transform(X, y)
        model_patch.assert_called_once()
        model_patch.return_value.fit.assert_called_once()
        model_patch.return_value.predict.assert_called_once()
