# runner.py
"""
SoamRunner Class
----------
A class that can execute all steps at once
and keep track of the whole run data
"""

from typing import List

from .step import Step


class SoamRunner:
    def __init__(self):
        """
        This object store a list of steps to execute in a pipelined way.
        its meant to store the configs of each run.
        """
        self.steps: List[Step] = None

    def run(self, data_in) -> None:
        """
        run each step run method in the correct way.
        """
        pass

    def add_step(self, step: Step) -> None:
        """
        add a step to the run and define the flow?
        """
        self.steps.append(step)
