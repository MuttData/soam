from darts.models import Theta
import numpy as np
import pandas as pd

from soam.workflow import Forecaster
from tests.helpers import sample_data_df  # pylint: disable=unused-import


def test_Forecaster(sample_data_df):  # pylint: disable=redefined-outer-name
    train_data = sample_data_df
    forecasting_model = Theta()
    fc = Forecaster(model=forecasting_model, output_length=10,)
    predictions, _, _ = fc.run(train_data)

    expected_predictions = pd.DataFrame.from_records(
        np.array(
            [
                ('2016-06-01T00:00:00.000000000', 452398.06308318),
                ('2016-07-01T00:00:00.000000000', 442252.57391223),
                ('2016-08-01T00:00:00.000000000', 454808.65212245),
                ('2016-09-01T00:00:00.000000000', 452284.15524087),
                ('2016-10-01T00:00:00.000000000', 459115.93494638),
                ('2016-11-01T00:00:00.000000000', 455217.41893568),
                ('2016-12-01T00:00:00.000000000', 445005.27185052),
                ('2017-01-01T00:00:00.000000000', 457635.98282733),
                ('2017-02-01T00:00:00.000000000', 455092.300957),
                ('2017-03-01T00:00:00.000000000', 461962.96254471),
            ],
            dtype=[('ds', '<M8[ns]'), ('yhat', '<f8')],
        )
    )
    pd.testing.assert_frame_equal(expected_predictions, predictions)
