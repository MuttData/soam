"""
Store results
----------
A class to store results in a table
"""

from muttlib.dbconn import BaseClient
import pandas as pd

from soam.core import Step


class Store(Step):
    def __init__(self, db_cli: BaseClient, table: str, db: str, **kwargs):
        """Store given data into a DataBase

        Parameters
        ----------
        db_cli:
            BaseClient client.
        table:
            str of table to store in.
        db:
            str of the database to use.
        """
        super().__init__(**kwargs)

        self.db_cli = db_cli
        self.table = table
        self.db = db
        self.extra_insert_args = {"table": self.table, "create_first": False}

    def run(self, df: pd.DataFrame):  # type: ignore
        """
        Store given data frame

        Parameters
        ----------
        df
            A pandas DataFrame to store.
        """

        return self.db_cli.insert_from_frame(df, self.db, **self.extra_insert_args,)
