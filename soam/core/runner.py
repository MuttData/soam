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
from typing import TYPE_CHECKING, Optional  # pylint:disable=unused-import

from prefect import Flow, Task

if TYPE_CHECKING:
    from soam.savers import Saver


class SoamFlow(Flow):
    def __init__(self, saver: "Optional[Saver]" = None, **kwargs):
        super().__init__(**kwargs)
        self.saver = saver
        self.start_datetime: datetime
        self.end_datetime: datetime
        if self.saver is not None:
            self.state_handlers.append(self.saver.save_flow_run)

    def add_task(self, task: Task) -> Task:
        if self.saver is not None:
            if self.saver.save_task_run not in task.state_handlers:
                task.state_handlers.append(self.saver.save_task_run)
        return super().add_task(task)
