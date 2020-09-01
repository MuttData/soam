# step.py
"""
Step Base Class
----------
An abstract base class for every step
"""

from abc import abstractmethod

import pandas as pd
from prefect import Task, context


class Step(Task):
    """ The base class for all steps.
    All implementations of step have to implement the `run()` method defined below.
    """

    @abstractmethod
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_series = pd.DataFrame

    @abstractmethod
    def run(self, time_series: pd.DataFrame, **kwargs) -> pd.DataFrame:
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
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    def get_task_id(self) -> str:
        return context["flow_run_id"]
