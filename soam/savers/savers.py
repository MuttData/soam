# savers.py
"""
Saver
----------
Saver is an abstract class used to store parameters and data through the
pipeline.
"""
from abc import ABC, abstractmethod
import datetime
import logging
from typing import List

from muttlib.utils import hash_str
from prefect import Task, context
from prefect.engine.state import State
from pydantic import BaseModel, Field, list, validator

from soam.core import SoamFlow, Step
from soam.data_models import StepTypeEnum
from soam.forecaster import Forecaster

logger = logging.getLogger(__name__)


class SoamFlowRunModel(BaseModel):

    id: str = None
    run_date: datetime.datetime = None
    start_time: datetime.datetime = None
    end_time: datetime.datetime = None

    @classmethod
    def fields_from_soamflow(cls, soamflow: SoamFlow):
        """
        Returns a dict that contains fields that could be inferred from a soamflow object.
        """
        return cls(
            id=context["flow_run_id"],
            start_time=soamflow.start_time,
            end_time=soamflow.end_time,
        )


class TaskRunModel(BaseModel):

    id: str = None
    params: str = None
    params_hash: str = None

    flow_run_id: str = None
    step_type: str = None

    run_date: datetime.datetime = None
    start_time: datetime.datetime = None
    end_time: datetime.datetime = None

    @classmethod
    def fields_from_task(cls, task: Task):
        # TODO: Here we should and the task for its children.
        return cls(
            id=context["task_run_id"],
            flow_run_id=context["flow_run_id"],
            params=repr(task),
            params_hash=hash_str(repr(task)),
            step_type=getattr(task, "step_type", None),
        )



class Saver(ABC):  # pylint:disable=abstract-method
    """ The base class for all savers objects.

    All implementations of Saver have to implement the state_handler of Prefect.
    Please check the [link](https://docs.prefect.io/core/concepts/states.html#state-handlers-callbacks)
    TODO: inherit from ABC or use ABCMeta to ensure abstractmethods implementation
    """

    @abstractmethod
    def __init__(self):  # pylint:disable=abstract-method
        pass


    def save_task_run_started(self, task_run_model = TaskRunModel):
        """
        This function will store the task run.
        """

    def save_task_run_ended(self, task_run_model = TaskRunModel):
        """
        This function will store the task run.
        """

    def save_task_run(self, task: Task, old_state: State, new_state: State):
        """
        This function will store the task run.
        """
        task_run_model = TaskRunModel.fields_from_task(task)
        if new_state.is_running():
            self.save_flow_run_started(task_run_model)
        if new_state.finished():
            self.save_flow_run_ended(task_run_model)

    def save_flow_run_started(self, soam_flow_run_model: SoamFlowRunModel):
        """
        Store the SoamFlow run.
        """

    def save_flow_run_ended(self, soam_flow_run_model: SoamFlowRunModel):
        """
        Store the SoamFlow run.
        """

    def save_flow_run(
        self, soamflow: SoamFlow, old_state: State, new_state: State
    ) -> State:
        """
        Save the SoamFlow run data in the create connection to a database.
        """
        soam_flow_run_model = SoamFlowRunModel.fields_from_soamflow(soamflow)
        if new_state.is_running():
            self.save_flow_run_started(soam_flow_run_model)
        if new_state.finished():
            # NOTE: There are multiple finished states we are not considering.
            # https://docs.prefect.io/api/latest/engine/state.html#state-2
            self.save_flow_run_ended(soam_flow_run_model)
