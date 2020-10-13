# slicer.py
"""
Slicer
----------
A class to create dataframes for aggregations
"""

from typing import (  # pylint:disable=unused-import
    TYPE_CHECKING,
    Dict,
    List,
    Optional,
    Union,
)

import pandas as pd

from soam.core import Step

if TYPE_CHECKING:
    from soam.savers import Saver


class Slicer(Step):
    def __init__(
        self,
        dimensions: Union[str, List[str]],
        savers: "Optional[List[Saver]]",
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

        self.dimensions = dimensions

    def run(self, raw_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:  # type: ignore
        """
        Slice the given dataframe with the dimensions setted.

        Parameters
        ----------
        raw_df
            A pandas DataFrame containing the raw data to slice
        Returns
        -------
        dict of {tuple of str: pd.DataFrame}
            key = dimmensions values,
            value = pandas DataFrame containing the sliced dataframes.

        """

        dataframes_ret = {}

        if self._check_dimensions(raw_df.columns.tolist()):
            for key, group in raw_df.groupby(self.dimensions):
                dataframes_ret[key] = group

        return dataframes_ret

    def _check_dimensions(self, columns: List[str]) -> bool:
        # flat_list = [item for sublist in for item in sublist]
        different_columns = set(self.dimensions) - set(columns)

        if len(different_columns) > 0:
            raise ValueError(
                f"Error unknown columns are setted in dimensions {different_columns}"
            )

        return True
