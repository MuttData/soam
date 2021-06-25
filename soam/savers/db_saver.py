"""Database saver."""
import logging

from muttlib.dbconn import BaseClient
from muttlib.utils import hash_str
from prefect import Task, context
from prefect.engine.state import State

from soam.core import SoamFlow
from soam.data_models import Base, ForecastValues, SoamFlowRunSchema, SoamTaskRunSchema
from soam.savers.savers import Saver
from soam.utilities.helpers import session_scope

logger = logging.getLogger(__name__)


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

    def save_forecast(self, task: Task, old_state: State, new_state: State) -> State:
        """
        Store the forecaster data in the constructed database.

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
            self.db_client.insert_from_frame(
                save_prediction, ForecastValues.__tablename__
            )

        return new_state

    def save_task_run(self, task: Task, old_state: State, new_state: State) -> State:
        """
        Store the task run information in the database.

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

    def save_flow_run(
        self, soamflow: SoamFlow, old_state: State, new_state: State
    ) -> State:
        """
        Save the SoamFlow run data in the create connection to a database.

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
