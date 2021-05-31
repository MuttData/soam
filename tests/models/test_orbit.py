from unittest.mock import MagicMock, patch

from pandas.testing import assert_frame_equal
import pytest

from soam.models.orbit import SkOrbit
from soam.utilities.utils import add_future_dates
from tests.helpers import sample_data_df  # pylint: disable=unused-import


def test_fit(sample_data_df):  # pylint: disable=redefined-outer-name
    with patch("soam.models.orbit.DLTFull") as model_patch:
        output_length = 10
        train_data = sample_data_df
        data = add_future_dates(train_data, output_length)
        X, y = data[data.columns[:-1]], data[data.columns[-1]]
        wrapper = SkOrbit()
        model_patch.assert_not_called()
        wrapper.fit(X, y)
        model_patch.assert_called_once()
        fit_call_df = model_patch.return_value.fit.call_args[0][0]
        assert_frame_equal(data, fit_call_df)


def test_predict_without_fit_fails(
    sample_data_df,
):  # pylint: disable=redefined-outer-name
    with patch("soam.models.orbit.DLTFull") as model_patch:
        output_length = 10
        train_data = sample_data_df
        data = add_future_dates(train_data, output_length)
        X = data[data.columns[:-1]]
        wrapper = SkOrbit()
        model_patch.assert_not_called()
        with pytest.raises(AttributeError):
            wrapper.predict(X)


def test_fit_transform(sample_data_df):  # pylint: disable=redefined-outer-name
    with patch("soam.models.orbit.DLTFull") as model_patch:
        output_length = 10
        train_data = sample_data_df
        data = add_future_dates(train_data, output_length)
        X, y = data[data.columns[:-1]], data[data.columns[-1]]
        wrapper = SkOrbit()
        model_patch.assert_not_called()
        wrapper.fit_transform(X, y)
        model_patch.assert_called_once()
        model_patch.return_value.fit.assert_called_once()
        model_patch.return_value.predict.assert_called_once()


def test_predict():
    X = MagicMock()
    wrapper = SkOrbit()
    model_mock = MagicMock()
    wrapper.model = model_mock
    wrapper.predict(X)
    model_mock.predict.assert_called_once_with(X)
    model_mock.predict.return_value.rename.assert_called_once_with(
        columns={"prediction": "yhat"}
    )
