"""
Slicer
----------
A class to create dataframes for aggregations
"""

import logging
from typing import List, Tuple, Union  # pylint:disable=unused-import

import pandas as pd
from pandas.core.common import maybe_make_list

from soam.constants import DS_COL
from soam.core import Step

COLUMN = "column"
GROUP = "group"
MODE = [GROUP, COLUMN]


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Slicer(Step):
    def __init__(
        self,
        dimensions: Union[str, List[str]] = [],
        metrics: Union[str, List[str]] = [],
        ds_col: str = DS_COL,
        keeps: Union[str, List[str]] = [],
        **kwargs,
    ):
        """Slice the incoming data upon the given dimensions

        Parameters
        ----------
        dimensions:
            str or list of str labels of categorical columns to slices
        """
        super().__init__(**kwargs)

        self.dimensions = maybe_make_list(dimensions)
        self.metrics = maybe_make_list(metrics)
        self.ds_col = ds_col
        self.keeps = maybe_make_list(keeps)

    def run(self, raw_df: pd.DataFrame) -> List[Tuple[str, pd.DataFrame]]:  # type: ignore
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

        Examples
        --------
        >>> df1 = pd.DataFrame(
        >>> {   "date": [1, 2, 1, 2, 3],
        >>>     "country": ["ARG", "ARG", "BRA", "BRA", "BRA"],
        >>>     "metric": [451, 213, 378, 754, 546]})
        >>> slicing_test = Slicer(metrics="metric", ds_col="date", dimensions="country")
        >>> slicing_test.run(df1)

        [   date country  metric
        0     1     ARG     451
        1     2     ARG     213,
            date country  metric
        2     1     BRA     378
        3     2     BRA     754
        4     3     BRA     546]
        """

        dataframes_ret = []

        if self._check_dimensions(raw_df.columns.tolist()):
            raw_df = raw_df.sort_values(by=self.ds_col)

            if self.dimensions:
                for dimension in self.dimensions:
                    dimension = maybe_make_list(dimension)
                    for _, group in raw_df.groupby(self.dimensions):
                        if self.metrics:
                            for metric in self.metrics:
                                metric = maybe_make_list(metric)
                                cols = [
                                    self.ds_col,
                                    *dimension,
                                    *metric,
                                    *self.keeps,
                                ]
                                dataframes_ret.append(group[cols])
                        else:
                            dataframes_ret.append(group)
            elif self.metrics:
                for metric in self.metrics:
                    metric = maybe_make_list(metric)
                    cols = [self.ds_col, *metric, *self.keeps]
                    dataframes_ret.append(raw_df[cols])
            else:
                raise ValueError("Error no dimension neither metric")

        logger.info("Dataframe sliced into %s pieces", len(dataframes_ret))
        return dataframes_ret

    def _check_dimensions(self, columns: List[str]) -> bool:
        # flat_list = [item for sublist in for item in sublist]
        different_columns = set(self.dimensions) - set(columns)
        different_columns.update(set([self.ds_col]) - set(columns))

        if len(different_columns) > 0:
            raise ValueError(
                f"""Error unknown columns are setted in dimensions
                or ds_col: {different_columns}"""
            )

        return True
