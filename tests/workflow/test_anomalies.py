"""Anomalies module tests."""

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from soam.workflow.anomalies import ConfidenceIntervalAnomaly
from tests.helpers import sample_data_df  # pylint:disable=unused-import

# pylint:disable=redefined-outer-name


@pytest.fixture
def prediction():
    return pd.DataFrame.from_records(
        np.array(
            [
                ('2016-03-01T00:00:00.000000000', 460093, 400000, 500000),
                ('2016-04-01T00:00:00.000000000', 300000, 290000, 400000),
                ('2016-05-01T00:00:00.000000000', 600000, 500000, 700000),
            ],
            dtype=[
                ('ds', '<M8[ns]'),
                ('yhat', '<i8'),
                ('yhat_lower', '<i8'),
                ('yhat_upper', '<i8'),
            ],
        ),
    )


@pytest.fixture
def expected_anomaly_df():
    return pd.DataFrame.from_records(
        np.array(
            [
                (
                    '2016-03-01T00:00:00.000000000',
                    460093,
                    460093,
                    400000,
                    500000,
                    False,
                    False,
                ),
                (
                    '2016-04-01T00:00:00.000000000',
                    450935,
                    300000,
                    290000,
                    400000,
                    False,
                    True,
                ),
                (
                    '2016-05-01T00:00:00.000000000',
                    471421,
                    600000,
                    500000,
                    700000,
                    True,
                    False,
                ),
            ],
            dtype=[
                ('ds', '<M8[ns]'),
                ('y', '<i8'),
                ('yhat', '<i8'),
                ('yhat_lower_y', '<i8'),
                ('yhat_upper_y', '<i8'),
                ('outlier_lower_y', 'bool'),
                ('outlier_upper_y', 'bool'),
            ],
        ),
    )


def test_confidence_interval_anomaly(sample_data_df, prediction, expected_anomaly_df):
    """ Test confidence interval based anomaly detector.
        Test that different outlier cases match with expected outputs.
    """
    detector = ConfidenceIntervalAnomaly(metric="y")
    anomaly_df = detector.run(time_series=sample_data_df, prediction=prediction)
    assert_frame_equal(anomaly_df, expected_anomaly_df)


def test_metric_not_present(sample_data_df, prediction):
    """Test that the ci_anomaly task raises appropiate exception on missing metric."""
    detector = ConfidenceIntervalAnomaly(metric="gmv")
    with pytest.raises(ValueError):
        detector.run(time_series=sample_data_df, prediction=prediction)
