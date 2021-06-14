from unittest.mock import patch

import mlflow

from soam.core import SoamFlow
from soam.workflow import Slicer
from tests.helpers import sample_data_df  # pylint: disable=unused-import


def test_simple_flow(sample_data_df, tmpdir):  # pylint: disable=redefined-outer-name
    tmp_path = "file://" + str(tmpdir) + "/mlruns"
    with patch("soam.core.runner.TRACKING_URI", tmp_path), patch(
        "soam.core.runner.TRACKING_IS_ACTIVE", True
    ), patch("soam.core.step.TRACKING_IS_ACTIVE", True):
        df = sample_data_df
        df['metric'] = 1
        dimensions = ["y"]
        ds_col = 'ds'
        metrics = ['metric']
        slice_task = Slicer(ds_col=ds_col, dimensions=dimensions, metrics=metrics)
        with SoamFlow(name="flow") as flow:
            _ = slice_task(sample_data_df)
        flow.run()
        log_df = mlflow.search_runs(['0'])
        assert len(log_df) == 2
        assert log_df['tags.mlflow.runName'].tolist() == ['Slicer', 'flow_run']
        slicer_logs = log_df[log_df['tags.mlflow.runName'] == 'Slicer'].iloc[0]
        assert slicer_logs['params.dimensions'] == str(dimensions)
        assert slicer_logs['params.metrics'] == str(metrics)
        assert slicer_logs['params.ds_col'] == str(ds_col)
