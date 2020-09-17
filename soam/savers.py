# savers.py
"""
Saver
----------
Saver is an abstract class used to store parameters and data through the
pipeline.
"""
import logging
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Union

import pandas as pd
from filelock import FileLock
from muttlib.dbconn import BaseClient
from muttlib.utils import hash_str, make_dirs
from prefect import Task, context
from prefect.engine.state import State

from soam.constants import FLOW_FILE_NAME, LOCK_NAME, PARENT_LOGGER
from soam.data_models import (
    Base,
    ForecastValues,
    SoamFlowRunSchema,
    SoamTaskRunSchema,
    StepTypeEnum,
)
from soam.forecaster import Forecaster
from soam.helpers import session_scope
from soam.runner import SoamFlow
from soam.utils import get_file_path

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


class Saver(ABC):  # pylint:disable=abstract-method
    """ The base class for all savers objects.

    All implementations of Saver have to implement the state_handler of Prefect.
    Please check the [link](https://docs.prefect.io/core/concepts/states.html#state-handlers-callbacks)
    TODO: inherit from ABC or use ABCMeta to ensure abstractmethods implementation
    """

    @abstractmethod
    def __init__(self):  # pylint:disable=abstract-method
        pass

    @abstractmethod
    def save_forecast(self, task: Task, old_state: State, new_state: State):
        """
        This function will store the forecasts values.
        """

    @abstractmethod
    def save_task_run(self, task: Task, old_state: State, new_state: State):
        """
        This function will store the task run.
        """

    @abstractmethod
    def save_flow_run(self, soamflow: SoamFlow, old_state: State, new_state: State):
        """
        Will store the SoamFlow run.
        """

    def get_task_type(self, task: Task):
        """

        Parameters
        ----------

        Return
        ----------

        """
        if isinstance(task, Forecaster):
            step_type = StepTypeEnum.forecast
        else:
            step_type = StepTypeEnum.custom
        return step_type


class CSVSaver(Saver):
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
        return self.flow_path / FLOW_FILE_NAME

    @property
    def flow_run_lock(self) -> Path:
        return self.flow_path / LOCK_NAME

    def save_forecast(self, task: Task, old_state: State,
                      new_state: State) -> State:
        """
        Store the forecaster data in the constructed path
        with the `{task_slug}_forecasts.csv`.
        """
        if new_state.is_successful():
            save_prediction = new_state.result[0].copy()
            save_prediction["task_run_id"] = context["task_run_id"]

            task_run_id = context["task_slug"] + "_" + context["task_run_id"]
            PREDICTION_CSV_SUFFIX = f"{task_run_id}_forecasts.csv"
            prediction_path = get_file_path(self.flow_path, PREDICTION_CSV_SUFFIX)

            save_prediction.to_csv(prediction_path, index=False)

        return new_state

    def save_task_run(self, task: Task, old_state: State,
                      new_state: State) -> State:
        """
        Store the task run information in the csv file created by `save_flow_run`
        """
        if new_state.is_successful():
            flow_run_file = self.flow_file_path
            lock = FileLock(self.flow_run_lock)

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

    def save_flow_run(self, soamflow: SoamFlow, old_state: State,
                      new_state: State) -> State:
        """
        Store the SoamFlow run information, create a folder for the run with a csv file.
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


class DBSaver(Saver):
    def __init__(self, base_client: BaseClient):
        """
        Create a DBSaver object and check if the database
        contains the tables it expect to store the data

        You can use a DBSaver for storing runs or runs + values.
        The values use the runs data as a Foreign Key.

        Parameters
        ----------
        base_client
            A BaseClient with connection to the database
        """
        super().__init__()
        self.db_client = base_client

        if base_client._connect() is not None:
            if not base_client.get_engine().has_table(ForecastValues.__tablename__):
                logger.error(
                    "There are no tables on this database"
                    "Please run: alembic revision --autogenerate "
                    "alembic upgrade head"
                )

    def save_forecast(self, task: Task, old_state: State,
                      new_state: State) -> State:
        """
        Store the forecaster data in the create connection to a database.
        """
        if new_state.is_successful():
            save_prediction = new_state.result[0].copy()
            save_prediction["task_run_id"] = context["task_run_id"]
            self.db_client.insert_from_frame(
                save_prediction, ForecastValues.__tablename__
            )

        return new_state

    def save_task_run(self, task: Task, old_state: State,
                      new_state: State) -> State:
        """
        Store the data of the task run in the create connection to a database.
        """
        if new_state.is_running():
            flow_run_id = context["flow_run_id"]
            task_run_id = context["task_run_id"]

            step_type = self.get_task_type(task)

            insert_fr = SoamTaskRunSchema(
                task_run_id=task_run_id,
                params=repr(task),
                params_hash=hash_str(repr(task)),
                step_type=step_type,
                flow_run_id=flow_run_id,
            )
            _ = self._insert_single(insert_fr)

        return new_state

    def save_flow_run(self, soamflow: SoamFlow, old_state: State,
                      new_state: State) -> State:
        """
        Save the SoamFlow run data in the create connection to a database.
        """
        if new_state.is_running():
            flow_run_id = context["flow_run_id"]
            run_date = context["date"]

            insert_fr = SoamFlowRunSchema(
                flow_run_id=flow_run_id,
                run_date=run_date,
                start_datetime=soamflow.start_datetime,
                end_datetime=soamflow.end_datetime,
            )

            _ = self._insert_single(insert_fr)

        return new_state

    def _insert_single(self, element: Base) -> int:
        with session_scope(engine=self.db_client.get_engine()) as session:
            session.add(element)  # pylint: disable=maybe-no-member

        return element
