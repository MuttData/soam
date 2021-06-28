# runner.py
"""
SoamFlow Class
--------------
A class that can execute the pipeline steps and keep track of the whole run
data

TODO: review if SoamFlow is going to be the only class that can run the
 pipeline
"""
from datetime import datetime
import logging
from typing import TYPE_CHECKING, Optional  # pylint:disable=unused-import

from prefect import Flow, Task

from soam.cfg import TRACKING_IS_ACTIVE, TRACKING_URI

logger = logging.getLogger(__name__)
try:
    from mlflow import end_run, set_tracking_uri, start_run
except ModuleNotFoundError:
    logger.debug("Mlflow dependency is not installed.")


if TYPE_CHECKING:
    from soam.savers.savers import Saver


class SoamFlow(Flow):
    """
    Soam Flow to execute the pipeline steps and keep track of the whole run data.
    SoamFlow is an extension of prefect.Flow to add tracking functionality.
    """

    def __init__(self, saver: "Optional[Saver]" = None, **kwargs):
        """
        Soam Flow init to execute pipeline steps and keep track of the run data.

        Parameters
        ----------
        saver: soam.savers.Saver
            The saver to store the pipeline steps and keep track of the whole run data.
        kwargs: dict
            extra args.
        """

        super().__init__(**kwargs)
        self.saver = saver
        self.start_datetime: datetime
        self.end_datetime: datetime
        if self.saver is not None:
            self.state_handlers.append(self.saver.save_flow_run)

        if TRACKING_IS_ACTIVE:
            self.active_run = None
            set_tracking_uri(TRACKING_URI)
            self.state_handlers.append(self.set_tracker_run)

    def add_task(self, task: Task) -> Task:
        """
        Adds the task and handlers to save the state.

        Parameters
        ----------
        task
            Represents a task where the flow is being executed.

        Returns
        -------
        super object
            Saves the task and the state handler.
        """
        if self.saver is not None:
            if self.saver.save_task_run not in task.state_handlers:
                task.state_handlers.append(self.saver.save_task_run)
        return super().add_task(task)

    def set_tracker_run(
        self, obj, old_state, new_state
    ):  # pylint: disable=unused-argument
        """
        Create a new mlflow run.

        Parameters
        ----------
        obj
            the underlying object to which this state handler is attached
        old_state
            the previous state of this object
        new_state
            the proposed new state of this object
        Returns
        -------
        newstate
            the new state of this object.
        """
        if new_state.is_running():
            obj.active_run = start_run(run_name="flow_run")
        if new_state.is_finished():
            end_run()
        return new_state
