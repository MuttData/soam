# step.py
"""
Step Base Class
---------------
An abstract base class for the steps in the pipeline, including: postprocess,
preprocess, extract and forecaster.
"""
from abc import abstractmethod
import logging

import pandas as pd
from prefect import Task, context
from sklearn.base import BaseEstimator

from soam.cfg import TRACKING_IS_ACTIVE
from soam.utilities.utils import flatten_dict

logger = logging.getLogger(__name__)
try:
    from mlflow import end_run, log_params, start_run
except ModuleNotFoundError:
    logger.debug("Mlflow dependency is not installed.")


class Step(Task, BaseEstimator):
    """
    The base class for all steps.
    All implementations of step have to implement the `run()` method defined below.
    """

    def __init__(self, **kwargs):
        """
        Soam Step init.

        Parameters
        ----------
        kwargs: dict
            extra args.
        """

        super().__init__(**kwargs)

        if TRACKING_IS_ACTIVE:
            self.active_run = None
            self.state_handlers.append(self.set_tracker_run)

    def get_params(self, deep=True):
        out = dict()
        for key in self._get_param_names():
            if key == "savers":
                continue
            value = getattr(self, key)
            if deep and hasattr(value, 'get_params'):
                deep_items = value.get_params().items()
                out.update((key + '__' + k, val) for k, val in deep_items)
            out[key] = value
        return out

    def get_mlflow_run_name(self):
        return f"{self.__class__.__name__}"

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
            obj.active_run = start_run(nested=True, run_name=self.get_mlflow_run_name())
            log_params(flatten_dict(self.get_params()))

        if new_state.is_finished():
            end_run()
        return new_state

    @abstractmethod
    def run(self) -> pd.DataFrame:
        """
        Execute this step function

        Parameters
        ----------
        time_series
            A pandas DataFrame containing the data for the step

        Returns
        -------
        pandas.DataFrame
            pandas DataFrame containing the output values.
        """

    def get_task_id(self) -> str:  # pylint: disable=no-self-use
        """
        Obtains the task id.

        Returns
        -------
        flow_run_id
            the id of the flow run.
        """
        return context["flow_run_id"]

    def __repr__(self) -> str:
        return f"<Task: {BaseEstimator.__repr__(self)}>"
