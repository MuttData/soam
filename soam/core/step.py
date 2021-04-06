# step.py
"""
Step Base Class
---------------
An abstract base class for the steps in the pipeline, including: postprocess,
preprocess, extract and forecaster.
"""
from abc import abstractmethod

import pandas as pd
from prefect import Task, context
from sklearn.base import BaseEstimator


class Step(Task, BaseEstimator):
    """
    The base class for all steps.
    All implementations of step have to implement the `run()` method defined below.
    """

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
