"""
MergeConcat
-----------
A class to merge or concat dataframes
"""

from typing import List, Union

import pandas as pd
from pandas.core.common import maybe_make_list

from soam.core import Step


class MergeConcat(Step):
    def __init__(
        self, keys: Union[str, List[str], None] = None, **kwargs,
    ):
        """
        Merge on concat dataframes dependending on the keys

        Parameters
        ----------
        keys:
            str or list of str labels of columns to merge on
        """
        super().__init__(**kwargs)

        if keys is None:
            keys = []
        self.keys = maybe_make_list(keys)
        self.complete_df = pd.DataFrame(columns=self.keys)

    def run(self, in_df: List[pd.DataFrame]) -> pd.DataFrame:  # type: ignore
        """
        If values of keys exist on in_df and complete_df will
        merge and add the in_df columns
        else will concat the in_df on the complete_df

        Parameters
        ----------
        in_df
            A pandas DataFrame containing the keys as columns

        Returns
        -------
        A pandas DataFrame
            with merged or concateneted data

        Examples
        --------
        >>> import pandas as pd
        >>> from soam.workflow import MergeConcat
        >>> df1 = pd.DataFrame({"date": [1], "metric1": [512]})
        >>> df2 = pd.DataFrame({"date": [1], "metric2": [328]})
        >>> df3 = pd.DataFrame({"date": [2], "metric1": [238]})
        >>> mc = MergeConcat(keys="date")
        >>> mc.run([df1,df2,df3])
        date	metric1	metric2
        1	    512.0	328.0
        2	    238.0	NaN
        """
        complete_df = pd.DataFrame(columns=self.keys)
        for df in in_df:
            if self._check_keys(df, complete_df):
                if set(df).issubset(set(complete_df.columns)):
                    complete_df = complete_df.combine_first(df)
                else:
                    complete_df = complete_df.merge(df, how="right", on=self.keys)
            else:
                complete_df = pd.concat([complete_df, df])

        return complete_df

    def _check_keys(self, in_df: pd.DataFrame, complete_df: pd.DataFrame) -> bool:
        """
        Check if keys values are in both in_df or complete_df
        """
        df_dict = in_df[self.keys].to_dict("list")
        return any(complete_df.isin(df_dict)[self.keys].all(axis=1))
