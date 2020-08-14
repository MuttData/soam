# runner.py
"""
SoamRunner Class
----------
A class that can execute all steps at once
and keep track of the whole run data
"""

from datetime import datetime
from typing import List

from .step import Step


class PipelineRun:
    def __init__(self):
        """
        This object store a list of steps to execute in a pipelined way.
        its meant to store the configs of each run.
        """
        self.steps: List[Step] = None
        self.start_datetime: datetime = None
        self.end_datetime: datetime = None

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


class StepRun:
    def __init__(self, step: Step, run_id: int):
        """
        This object is an intermediate object for the steps and the run
        """
        self.step: Step = step
        self.run_id: int = run_id
