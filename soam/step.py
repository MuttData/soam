# step.py
"""
Step Base Class
----------
An abstract base class for every step
"""

from abc import ABC, abstractmethod

import pandas as pd


class Step(ABC):
    """ The base class for all steps.
    All implementations of step have to implement the `run()` method defined below.
    """

    @abstractmethod
    def __init__(self):
        self.time_series = pd.DataFrame

    @abstractmethod
    def run(self, time_series: pd.DataFrame) -> pd.DataFrame:
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
