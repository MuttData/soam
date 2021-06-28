"""CSV saver."""
from pathlib import Path
from typing import Union

from filelock import FileLock
from muttlib.utils import make_dirs
import pandas as pd
from prefect import Task, context
from prefect.engine.state import State

from soam.constants import FLOW_FILE_NAME, LOCK_NAME
from soam.core import SoamFlow
from soam.savers.savers import Saver
from soam.utilities.utils import get_file_path


class CSVSaver(Saver):
    """
    CSV Saver object to store the predictions and the runs.
    """

    def __init__(self, path: Union[str, Path]):
        """
        Create a saver object to store the predcitions and the runs.

        You can use a CSVSaver for storing runs and/or values.

        Parameters
        ----------
        path
            str or pathlib.Path where the file will be created.
        """
        super().__init__()
        self.path = Path(make_dirs(path))

    @property
    def flow_path(self) -> Path:
        """
        Generation of the flow run folder directory.

        Parameters
        ----------
        Path
            str where the file will be created.

        Returns
        -------
        path
            Path of the directory of the flow run folder.
        """
        flow_run_folder = (
            context["flow_name"]
            + "_"
            + context["date"].replace(microsecond=0, tzinfo=None).isoformat()
            + "_"
            + context["flow_run_id"]
        )

        return make_dirs(self.path / flow_run_folder)

    @property
    def flow_file_path(self) -> Path:
        """
        Flow file name upon the path.

        Parameters
        ----------
        Path
            str where the file will be created.

        Returns
        -------
        path
            Path of the flow file.
        """
        return self.flow_path / FLOW_FILE_NAME

    @property
    def flow_run_lock(self) -> Path:
        """
        Flow run lock upon the path.

        Parameters
        ----------
        Path
            str where the file will be created.

        Returns
        -------
        path
            Path of the lock name.
        """
        return self.flow_path / LOCK_NAME

    def save_forecast(self, task: Task, old_state: State, new_state: State) -> State:
        """
        Store the forecaster data in the constructed path
        with the `{task_slug}_forecasts.csv`.

        Parameters
        ----------
        task: Task
            Specify the forecast task you want to save information of.
        old_state: State
            Task old state.
        new_state : State
            Task new state.

        Returns
        -------
        State
            The new updated state of the forecast task.
        """
        if new_state.is_successful():
            save_prediction = new_state.result[0].copy()
            save_prediction["task_run_id"] = context["task_run_id"]

            task_run_id = context["task_slug"] + "_" + context["task_run_id"]
            PREDICTION_CSV_SUFFIX = f"{task_run_id}_forecasts.csv"
            prediction_path = get_file_path(self.flow_path, PREDICTION_CSV_SUFFIX)

            save_prediction.to_csv(prediction_path, index=False)

        return new_state

    def save_task_run(self, task: Task, old_state: State, new_state: State) -> State:
        """
        Store the task run information in the csv file created by `save_flow_run`

        Parameters
        ----------
        task: Task
            Specify the task you want to save information of.
        old_state: State
            Task old state.
        new_state : State
            Task new state.

        Returns
        -------
        State
            The new updated state of the task.
        """
        if new_state.is_successful():
            flow_run_file = self.flow_file_path
            lock = FileLock(str(self.flow_run_lock))

            with lock.acquire(timeout=5):
                read_df = pd.read_csv(flow_run_file)
                flow_values = read_df[read_df.flow_state.str.contains("Running")].iloc[
                    0
                ]
                csv_data = {
                    "flow_run_id": [flow_values["flow_run_id"]],
                    "start_datetime": [flow_values["start_datetime"]],
                    "end_datetime": [flow_values["end_datetime"]],
                    "flow_state": [flow_values["flow_state"]],
                    "task_run_id": [context["task_run_id"]],
                    "repr_task": [repr(task)],
                }

                df = pd.DataFrame.from_dict(csv_data)
                df.to_csv(flow_run_file, mode="a", header=False, index=False)

        return new_state

    def save_flow_run(
        self, soamflow: SoamFlow, old_state: State, new_state: State
    ) -> State:
        """
        Store the SoamFlow run information, create a folder for the run with a csv file.

        Parameters
        ----------
        saomflow: SoamFlow
            Specify the soamflow you want to save information of.
        old_state: State
            SoamFlow old state.
        new_state : State
            SoamFlow new state.

        Returns
        -------
        State
            The new updated state of the SoamFlow.
        """
        if new_state.is_running():
            csv_data = {
                "flow_run_id": [context["flow_run_id"]],
                "start_datetime": [soamflow.start_datetime],
                "end_datetime": [soamflow.start_datetime],
                "flow_state": [new_state.message],
                "task_run_id": None,
                "repr_task": None,
            }

            df = pd.DataFrame.from_dict(csv_data)
            df.to_csv(self.flow_file_path, index=False)

        elif new_state.is_successful() or new_state.is_failed():
            self.flow_run_lock.unlink()

        return new_state
