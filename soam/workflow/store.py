"""
Store results
----------
A class to store results in a table
"""

from typing import Dict

from muttlib.dbconn import BaseClient
import pandas as pd

from soam.core import Step


class Store(Step):
    def __init__(
        self, db_cli: BaseClient, table: str, extra_insert_args: Dict = None, **kwargs
    ):
        """Store given data into a DataBase

        Parameters
        ----------
        db_cli:
            BaseClient client.
        table:
            str of table to store in.
        extra_insert_args:
            dict extra arguments to insert data.
        """
        super().__init__(**kwargs)

        self.db_cli = db_cli
        self.table = table
        self.extra_insert_args = extra_insert_args

    def run(self, df: pd.DataFrame):  # type: ignore
        """
        Store given data frame

        Parameters
        ----------
        df
            A pandas DataFrame to store.
        """
        if not self.extra_insert_args:
            self.extra_insert_args = {}

        return self.db_cli.insert_from_frame(
            df=df, table=self.table, **self.extra_insert_args
        )
