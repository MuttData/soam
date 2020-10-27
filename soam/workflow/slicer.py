# slicer.py
"""
Slicer
----------
A class to create dataframes for aggregations
"""

from typing import (  # pylint:disable=unused-import
    TYPE_CHECKING,
    List,
    Optional,
    Tuple,
    Union,
)

import pandas as pd
from pandas.core.common import maybe_make_list

from soam.constants import DS_COL
from soam.core import Step

if TYPE_CHECKING:
    from soam.savers import Saver


COLUMN = "column"
GROUP = "group"
MODE = [GROUP, COLUMN]


class Slicer(Step):
    def __init__(
        self,
        dimensions: Union[str, List[str]],
        mode: str,
        ds_col: str = DS_COL,
        savers: "Optional[List[Saver]]" = None,
        **kwargs,
    ):
        """Slice the incoming data upon the given dimensions

        Parameters
        ----------
        dimensions:
            str or list of str labels of categorical columns to slices
        savers:
            list of soam.savers.Saver, optional
            The saver to store the parameters and state changes.
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:
                self.state_handlers.append(saver.save_forecast)
                # TODO modify saver to save step abstraction
                # self.state_handlers.append(saver.save_sliced)

        self.dimensions = maybe_make_list(dimensions)
        self.mode = mode
        self.ds_col = ds_col

    def run(self, raw_df: pd.DataFrame) -> List[Tuple[str, pd.DataFrame]]:
        """
        Slice the given dataframe with the dimensions setted.

        Parameters
        ----------
        raw_df
            A pandas DataFrame containing the raw data to slice
        Returns
        -------
        list of (tuple of str: pd.DataFrame)
            key = dimmensions values,
            value = pandas DataFrame containing the sliced dataframes.

        """

        dataframes_ret = []

        if self._check_dimensions(raw_df.columns.tolist()):
            if self.mode == GROUP:
                for key, group in raw_df.groupby(self.dimensions):
                    dataframes_ret.append((key, group))
            elif self.mode == COLUMN:
                for dimension in self.dimensions:
                    dataframes_ret.append((dimension, raw_df[[self.ds_col, dimension]]))
            else:
                raise ValueError(f"Error unknown mode: {self.mode}, allowed: {MODE}")

        return dataframes_ret

    def _check_dimensions(self, columns: List[str]) -> bool:
        # flat_list = [item for sublist in for item in sublist]
        different_columns = set(self.dimensions) - set(columns)
        different_columns.update(set(self.ds_col) - set(columns))

        if len(different_columns) > 0:
            raise ValueError(
                f"""Error unknown columns are setted in dimensions
                or ds_col: {different_columns}"""
            )

        return True
