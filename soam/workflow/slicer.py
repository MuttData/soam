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
        extra_regressors=False,
        metrics_as_regressors=False,
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
        self.extra_regressors = extra_regressors
        if metrics_as_regressors and not extra_regressors:
            raise ValueError(
                "extra_regressors must be True for metrics to be regressors."
            )
        self.metrics_as_regressors = metrics_as_regressors

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
        >>>     "metric2": [333, 444, 555, 666, 777]})
        >>> slicing_test = Slicer(metrics="metric", ds_col="date", dimensions="country" \
                            metrics=["metric", "metric2"])
        >>> slicing_test.run(df1)

        [   date country  metric
        0     1     ARG     451
        1     2     ARG     213,
            date country  metric
        2     1     BRA     378
        3     2     BRA     754
        4     3     BRA     546,
            date country  metric2
        0     1     ARG     333
        1     2     ARG     444,
            date country  metric2
        2     1     BRA     555
        3     2     BRA     666
        4     3     BRA     777]
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
                                if self.extra_regressors:
                                    extra_metrics = self._get_disjoint_metrics(
                                        metric, self.metrics
                                    )
                                    cols = [
                                        self.ds_col,
                                        *dimension,
                                        *metric,
                                        *extra_metrics,
                                        *self.keeps,
                                    ]
                                    metric_df = self._rename_cols(
                                        df=group[cols],
                                        y=metric,
                                        extra=extra_metrics + self.keeps,
                                    )
                                else:
                                    cols = [
                                        self.ds_col,
                                        *dimension,
                                        *metric,
                                        *self.keeps,
                                    ]
                                    metric_df = group[cols]
                                dataframes_ret.append(metric_df)
                        else:
                            dataframes_ret.append(group)
            elif self.metrics:
                for metric in self.metrics:
                    if self.extra_regressors:
                        metric = maybe_make_list(metric)
                        extra_metrics = self._get_disjoint_metrics(metric, self.metrics)
                        cols = [self.ds_col, *metric, *extra_metrics, *self.keeps]
                        metric_df = self._rename_cols(
                            df=raw_df[cols], y=metric, extra=extra_metrics + self.keeps,
                        )
                    else:
                        metric = maybe_make_list(metric)
                        cols = [self.ds_col, *metric, *self.keeps]
                        metric_df = raw_df[cols]
                    dataframes_ret.append(metric_df)
            else:
                raise ValueError("Error no dimension neither metric")

        logger.info("Dataframe sliced into %s pieces", len(dataframes_ret))
        return dataframes_ret

    def _check_dimensions(self, columns: List[str]) -> bool:
        """Check if the dimensions and ds columns are in the dataframe"""
        different_columns = set(self.dimensions) - set(columns)
        different_columns.update(set([self.ds_col]) - set(columns))

        if len(different_columns) > 0:
            raise ValueError(
                f"""Error unknown columns are setted in dimensions
                or ds_col: {different_columns}"""
            )

        return True

    def _get_disjoint_metrics(
        self, metric: List[str], metric_list: List[str]
    ) -> List[str]:
        """Generate list of metris without first metric."""
        if not self.metrics_as_regressors:
            return []
        return list(set(metric_list) - set(metric))

    def _rename_cols(
        self, df: pd.DataFrame, y: List[str], extra=List[str]
    ) -> pd.DataFrame:
        """Rename DataFrame columns with y_ or r_ prefixes."""
        y_cols = [f"y_{y_col}" for y_col in y]
        r_cols = [f"r_{r_col}" for r_col in extra]

        mapping = dict(zip(y + extra, y_cols + r_cols))

        return df.rename(mapping, axis=1)
