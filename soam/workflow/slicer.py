"""
Slicer
------
A class to create dataframes for aggregations
"""

import logging
from typing import List, Tuple, Union

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
        dimensions: Union[str, List[str], None] = None,
        metrics: Union[str, List[str], None] = None,
        ds_col: str = DS_COL,
        keeps: Union[str, List[str], None] = None,
        **kwargs,
    ):
        """
        Slice the incoming data upon the given dimensions

        Parameters
        ----------
        dimensions:
            str or list of str labels of categorical columns to slices
        metrics:
            str or list of str labels of metrics columns to slices
        ds_col:
            str of datetime column
        keeps:
            str or list of str labels of columns to keep.
        """
        if dimensions is None:
            dimensions = []
        if metrics is None:
            metrics = []
        if keeps is None:
            keeps = []
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
        list[pd.DataFrame]
            DataFrame containing the sliced dataframes.

        Examples
        --------
        >>> df1 = pd.DataFrame(
        >>> {   "date": [1, 2, 1, 2, 3],
        >>>     "country": ["ARG", "ARG", "BRA", "BRA", "BRA"],
        >>>     "color": ["blue", "red", "red", "blue", "blue"],
        >>>     "metric": [451, 213, 378, 754, 546]})
        >>>     "metric2": [333, 444, 555, 666, 777]})
        >>> slicing_test = Slicer(metrics=["metric", "metric2"], ds_col="date", \
                            dimensions=["country","color", ["country","color"]] )
        >>> slicing_test.run(df1)

        [
        date country  metric
          1     ARG     451
          2     ARG     213,
        date country  metric2
          1     ARG      333
          2     ARG      444,
        date country  metric
          1     BRA     378
          2     BRA     754
          3     BRA     546,
        date country  metric2
          1     BRA      555
          2     BRA      666
          3     BRA      777,
        date color  metric
          1  blue     451
          2  blue     754
          3  blue     546,
        date color  metric2
          1  blue      333
          2  blue      666
          3  blue      777,
        date color  metric
          1   red     378
          2   red     213,
        date color  metric2
          1   red      555
          2   red      444,
        date country color  metric
          1     ARG  blue     451,
        date country color  metric2
          1     ARG  blue      333,
        date country color  metric
          2     ARG   red     213,
        date country color  metric2
          2     ARG   red      444,
        date country color  metric
          2     BRA  blue     754
          3     BRA  blue     546,
        date country color  metric2
          2     BRA  blue      666
          3     BRA  blue      777,
        date country color  metric
          1     BRA   red     378,
        date country color  metric2
          1     BRA   red      555]

        """

        dataframes_ret = []

        # Validate logic
        self._check_dimensions(raw_df.columns.tolist())
        if not self.dimensions or not self.metrics:
            raise ValueError("Error no dimension neither metric")

        # Setup dimensinal groups
        raw_df = raw_df.sort_values(by=self.ds_col)

        if self.dimensions:
            groups = []
            for dimension in self.dimensions:
                groups.extend([(g[1], dimension) for g in raw_df.groupby(dimension)])
        else:
            groups = [(raw_df, [])]

        # Make the cuts
        for group, dimension in groups:
            for metric in self.metrics:
                cols = [
                    self.ds_col,
                    *maybe_make_list(dimension),
                    *maybe_make_list(metric),
                    *self.keeps,
                ]
                dataframes_ret.append(group[cols])
        logger.info("Dataframe sliced into %s pieces", len(dataframes_ret))
        return dataframes_ret

    def _check_dimensions(self, columns: List[str]):
        """Check if the dimensions and ds columns are in the dataframe"""
        dimensions = []
        for dim in self.dimensions:
            dimensions.extend(maybe_make_list(dim))
        different_columns = set(dimensions) - set(columns)
        different_columns.update(set([self.ds_col]) - set(columns))

        if len(different_columns) > 0:
            raise ValueError(
                f"""Error unknown columns are setted in dimensions
                or ds_col: {different_columns}"""
            )
