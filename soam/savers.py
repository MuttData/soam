"""
Saver
----------
`Saver` is an abstract class that create a way to save values.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
import logging
from pathlib import Path
from typing import Union

from muttlib.dbconn import BaseClient
from muttlib.utils import hash_str
import pandas as pd
from soam.constants import PARENT_LOGGER
from soam.data_models import AbstractIDBase, ForecasterRuns, ForecastValues
from sqlalchemy import engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


class Saver(ABC):
    """ The base class for all savers objects.

    All implementations of Saver have to implement the `save()` method defined below.
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def save(self, prediction: pd.DataFrame, model_data: str) -> int:
        """
        This function will store the given data and the model parameters
        
        Parameters
        ----------
        prediction
            A pandas DataFrame with the predicted values.
        model_data
            A string with the model name and it's parameters.
        """
        pass


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

    def save(self, prediction: pd.DataFrame, model_data: str) -> int:
        """
        Store the given data in the constructed path
        with the `prediction.csv`.

        If the path does not exist, it will be created.

        Parameters
        ----------
        prediction
            A pandas DataFrame with the predicted values.
        model_data
            A string with the model name and it's parameters.
        Returns
        -------
        int
            The id number

        """
        PREDICTION_CSV = "_prediction.csv"
        max_index = 0

        self.path.mkdir(parents=True, exist_ok=True)
        prediction.set_index

        if not (self.path / ("0" + PREDICTION_CSV)).is_file():
            prediction_path = self.path / ("0" + PREDICTION_CSV)

        else:
            predictions_files = self.path.glob("*_prediction.csv")
            max_index = (
                max(int(pred.name.split("_")[0]) for pred in predictions_files) + 1
            )
            prediction_path = self.path / (str(max_index) + PREDICTION_CSV)

        prediction.to_csv(prediction_path, index=False)

        return max_index


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

    def save(self, prediction: pd.DataFrame, model_data: str) -> int:
        """
        Store the given data in the database for the schemas please check data_models.
        The database migrations use alembic
        
        Parameters
        ----------
        prediction
            A pandas DataFrame with the predicted values.
        model_data
            A string with the model name and it's parameters.
        Returns
        -------
        int
            The id number
        """
        insert_fr = ForecasterRuns(params=model_data, params_hash=hash_str(model_data))
        run_id = self._insert_single(insert_fr)

        prediction["run_id"] = run_id
        self.db_client.insert_from_frame(prediction, ForecastValues.__tablename__)

        return run_id

    def _insert_single(self, element: AbstractIDBase) -> int:
        with session_scope(engine=self.db_client.get_engine()) as session:
            session.add(element)
            session.flush()
            run_id = element.id

        return run_id


# TODO remove this function when added to muttlib
@contextmanager
def session_scope(engine: engine.Engine, **session_kw):
    """Provide a transactional scope around a series of operations."""

    Session = sessionmaker(bind=engine)
    session = Session(**session_kw)

    try:
        yield session
        session.commit()
    except Exception as err:
        logger.exception(err)
        session.rollback()
        raise
    finally:
        session.close()
