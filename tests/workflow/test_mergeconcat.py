"""Merge concat tester"""
import pandas as pd
from pandas._testing import assert_frame_equal

from soam.workflow import MergeConcat


def test_merge_concat():
    """Function to test the merge concat."""
    df1 = pd.DataFrame({"date": [1], "metric1": [512]})
    df2 = pd.DataFrame({"date": [1], "metric2": [328]})
    df3 = pd.DataFrame({"date": [2], "metric1": [238]})

    dict_result = {
        "date": [1, 2],
        "metric1": [512.0, 238.0],
        "metric2": [328.0, None],
    }
    df_result = pd.DataFrame(dict_result, index=[0, 1])

    mc = MergeConcat(keys="date")
    df_concated = mc.run([df1, df2, df3])

    assert_frame_equal(
        df_result.reset_index(drop=True),
        df_concated.reset_index(drop=True),
        check_dtype=False,
    )
