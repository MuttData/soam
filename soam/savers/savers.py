# savers.py
"""
Saver
-----
Saver is an abstract class used to store parameters and data through the
pipeline.
"""
from abc import ABC, abstractmethod
import logging

from prefect import Task
from prefect.engine.state import State

from soam.core import SoamFlow
from soam.data_models import StepTypeEnum
from soam.workflow import Forecaster

logger = logging.getLogger(__name__)


class Saver(ABC):  # pylint:disable=abstract-method
    """
    The base class for all savers objects.

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
        task: Task
            Specified task to get the type of.

        Return
        ------
        str
            Step type of the task.
        """
        if isinstance(task, Forecaster):
            step_type = StepTypeEnum.forecast
        else:
            step_type = StepTypeEnum.custom
        return step_type
