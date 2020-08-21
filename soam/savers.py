"""
Saver
----------
`Saver` is an abstract class that create a way to save values.
"""
from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Union

from muttlib.dbconn import BaseClient
from muttlib.utils import hash_str, make_dirs
from soam.constants import PARENT_LOGGER
from soam.data_models import (
    AbstractIDBase,
    ForecastValues,
    PipelineRunSchema,
    StepRunSchema,
    StepTypeEnum
)
from soam.forecaster import Forecaster
from soam.helpers import session_scope
from soam.runner import PipelineRun, StepRun
from soam.step import Step
from soam.utils import get_file_path

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


class Saver(ABC):
    """ The base class for all savers objects.

    All implementations of Saver have to implement the `save()` method defined below.
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def save_forecaster_impl(self, forecaster: Forecaster):
        """
        This function will store the given data and the model from the forecaster.

        Parameters
        ----------
        forecaster
            A Forecaster object to store its data and model config.
        """

    def save_single_step(self, step: Step, run_id: str):
        """
        Store the step data.

        Parameters
        ----------
        step
            A Step object (such as a Forecaster) to store its data and model config.
        run_id
            Name of the pipeline created to store only this run.
        """
        pipeline_run = PipelineRun(run_id)
        self.save_pipeline_run(pipeline_run)
        step_run = StepRun(step, pipeline_run)
        self.save_step_run(step_run)

    def save_pipeline_run(self, pipeline_run: PipelineRun):
        """Save a pipeline run object without steps.

        Args:
            pipeline_run (PipelineRun): PipelineRun object.
        """

    @abstractmethod
    def save_step_run(self, step_run: StepRun):
        """Save a StepRun.

        This function should use get_step_save_op and get_step_type to save the
        Step data.

        Args:
            step_run (StepRun): Step data.
        """


    def get_step_save_op(self, step: Step):
        save_ops = {StepTypeEnum.forecast: self.save_forecaster_impl}
        step_type = self.get_step_type(step)
        save_op = save_ops.get(step_type, self.save_noop)
        return save_op

    def save_noop(self, *args, **kwargs):
        pass

    def get_step_type(self, step: Step):
        if isinstance(step, Forecaster):
            step_type = StepTypeEnum.forecast
        else:
            step_type = StepTypeEnum.custom
        return step_type


class CSVSaver(Saver):
    def __init__(self, path: Union[str, Path]):
        """
        Create a saver object to store the predicted data in a csv file

        Parameters
        ----------
        path
            str or pathlib.Path where the file will be created.
        filename
            A string with file name.
        """
        self.path = Path(path)

    def save_step_run(self, step_run: StepRun):
        """Save a step run data to csv.

        Args:
            step_run (StepRun): Step data.
        """
        save_op = self.get_step_save_op(step_run.step)
        save_op(step_run.step, step_run.pipeline_run.run_id)

    def save_forecaster_impl(self, forecaster: Forecaster, run_id: str):
        """
        Store the forecaster data in the constructed path
        with the `prediction.csv`.

        If the path does not exist, it will be created.

        Parameters
        ----------
        forecaster
            A Forecaster object to store its data and model config.
        Returns
        """
        PREDICTION_CSV_SUFFIX = f"{run_id}_prediction.csv"
        _ = make_dirs(self.path)
        prediction_path = get_file_path(self.path, PREDICTION_CSV_SUFFIX)
        forecaster.prediction.to_csv(prediction_path, index=False)


class DBSaver(Saver):
    def __init__(self, base_client: BaseClient):
        """
        Create a DBSaver object and check if the database
        contains the tables it expect to store the data

        Parameters
        ----------
        base_client
            A BaseClient with connection to the database
        """
        self.db_client = base_client

        if base_client._connect() is not None:
            if not base_client.get_engine().has_table(ForecastValues.__tablename__):
                logger.error(
                    "There are no tables on this database"
                    "Please run: alembic revision --autogenerate "
                    "alembic upgrade head"
                )

    def save_forecaster_impl(self, forecaster: Forecaster, step_run_id: int):
        save_prediction = forecaster.prediction.copy()
        save_prediction["step_run_id"] = step_run_id
        self.db_client.insert_from_frame(save_prediction, ForecastValues.__tablename__)

    def save_step_run(self, step_run: StepRun):
        """
        Save the forecaster run configuration
        """
        save_op = self.get_step_save_op(step_run)
        step_type = self.get_step_type(step_run)

        run_id = self.get_pipeline_run_id(step_run.pipeline_run)
        insert_fr = StepRunSchema(
            params=repr(step_run),
            params_hash=hash_str(repr(step_run)),
            step_type=step_type,
            run_id=run_id,
        )
        step_run_id = self._insert_single(insert_fr)
        save_op(step_run.step, step_run_id)

    def save_pipeline_run(self, pipeline_run: PipelineRun):
        """
        Save the forecaster run configuration
        """
        insert_fr = PipelineRunSchema(
            run_id=pipeline_run.run_id,
            start_datetime=pipeline_run.start_datetime,
            end_datetime=pipeline_run.end_datetime,
        )
        self._insert_single(insert_fr)

    def get_pipeline_run_id(self, pipeline_run: PipelineRun):
        if pipeline_run is None:
            return None
        with session_scope(engine=self.db_client.get_engine()) as session:
            pr = (
                session.query(PipelineRunSchema)
                .filter(PipelineRunSchema.run_id == pipeline_run.run_id)
                .one_or_none()
            )
            rv = None if pr is None else pr.id
            return rv

    def _insert_single(self, element: AbstractIDBase) -> int:
        with session_scope(engine=self.db_client.get_engine()) as session:
            session.add(element)
            session.flush()
            run_id = element.id

        return run_id

