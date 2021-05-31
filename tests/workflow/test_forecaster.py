"""Forecaster tester."""
import numpy as np
import pandas as pd

from soam.models.prophet import SkProphet
from soam.utilities.utils import add_future_dates
from soam.workflow import Forecaster
from tests.helpers import sample_data_df  # pylint: disable=unused-import


def test_forecaster(sample_data_df):  # pylint: disable=redefined-outer-name
    """Function to test the forecaster on sample data."""
    output_length = 10
    train_data = sample_data_df
    data = add_future_dates(train_data, output_length)
    forecasting_model = SkProphet()
    fc = Forecaster(model=forecasting_model, output_length=output_length,)
    predictions, _, _ = fc.run(data)

    expected_predictions = pd.DataFrame.from_records(
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
            dtype=[('ds', '<M8[ns]'), ('yhat', '<f8')],
        )
    )
    pd.testing.assert_frame_equal(expected_predictions, predictions)


def test_forecaster_custom_response_col(
    sample_data_df: pd.DataFrame,  # pylint: disable=redefined-outer-name
):
    response_col = "value"
    ds_col = "date"
    output_length = 10
    train_data = sample_data_df.rename({"y": response_col, "ds": ds_col}, axis=1)
    data = add_future_dates(train_data, output_length, ds_col=ds_col)
    forecasting_model = SkProphet(ds_col=ds_col)
    fc = Forecaster(
        model=forecasting_model,
        ds_col=ds_col,
        output_length=output_length,
        response_col=response_col,
    )
    predictions, _, _ = fc.run(data)

    expected_predictions = pd.DataFrame.from_records(
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
            dtype=[('date', '<M8[ns]'), ("yhat", '<f8')],
        )
    )
    pd.testing.assert_frame_equal(expected_predictions, predictions)
