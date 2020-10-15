import logging

from muttlib.dbconn import BaseClient
from muttlib.utils import hash_str
from prefect import Task, context
from prefect.engine.state import State

from soam.core import SoamFlow
from soam.data_models import Base, ForecastValues, SoamFlowRunSchema, SoamTaskRunSchema
from soam.savers import Saver, SoamFlowRunModel, TaskRunModel
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

    def save_forecast(self, task: Task, old_state: State, new_state: State) -> State:
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

    def save_task_run_ended(self, task_run_model = TaskRunModel):
        # Here we should take the task's children and build a structure that makes it easier to add them.
        insert_fr = SoamTaskRunSchema(**task_run_model.dict())
        self._insert_single(insert_fr)

    def save_task_run_started(self, task_run_model = TaskRunModel):
        insert_fr = SoamTaskRunSchema(**task_run_model.dict())
        self._insert_single(insert_fr)

    def save_flow_run_started(self, soam_flow_run_model: SoamFlowRunModel):
        insert_fr = SoamFlowRunSchema(**soam_flow_run_model.dict())
        self._insert_single(insert_fr)

    def _insert_single(self, element: Base) -> int:
        with session_scope(engine=self.db_client.get_engine()) as session:
            session.add(element)  # pylint: disable=maybe-no-member

        return element
