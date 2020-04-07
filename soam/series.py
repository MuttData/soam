import json
import logging

from soam.constants import DS_COL
from soam.helpers import AttributeHelperMixin
from soam.utils import sanitize_arg_empty_dict

logger = logging.getLogger(__name__)


class SeriesManager(AttributeHelperMixin):
    def __init__(self, series_dict=None):
        self.series_dict = sanitize_arg_empty_dict(series_dict)
        self.regressors_l = []  # type: ignore

    # def transform(self, kpi, time_granularity, factor_mgr):
    #     self.series_dict = transform_pipeline(
    #         self.series_dict, kpi, time_granularity, factor_mgr
    #     )

    def __getitem__(self, k):
        return self.series_dict[k]

    def __setitem__(self, k, v):
        self.series_dict[k] = v

    def items(self):
        return self.series_dict.items()

    def build_regressors(self):
        self.regressors_l = create_regressors_pipeline(self.series_dict)

    def validate(self, time_granularity, ds_col=DS_COL, accept_empty=True):
        # TODO: This check is also present in coseries. Factor it out.
        for k, df in self.series_dict.items():
            if df.empty:
                msg = f"Series {k} is empty."
                if accept_empty:
                    logger.warning(msg)
                else:
                    raise ValueError(msg)
            else:
                if df[ds_col].dt.round(time_granularity).unique().shape[0] != len(df):
                    raise ValueError(
                        f"{ds_col} in dimension {k} has non-unique values."
                    )


class FactorManager(AttributeHelperMixin):
    def __init__(
        self,
        factor_col,
        # geo_granularity=NATIONAL_GEO_GRANULARITY,
        # max_levels_num=MAX_FACTOR_LEVELS,
    ):
        # self.geo_granularity = geo_granularity
        # self.max_levels_num = max_levels_num
        self.target_series = None

        # The default case is to have an empty factor_col thus return no query or levels
        if factor_col.strip(" ") == "":
            factor_col = None
        self.factor_col = factor_col
        self.factor_levels = [None]

        self.factor_query = None
        self.target_series = None

        # FIXME: Ideally we would want `granularity` to be a list of columns used for factorization.
        self.granularity = [self.factor_col]

        # assert self.geo_granularity in GEO_GRANULARITIES, logger.error(  # type: ignore
        #     f"Bad geo granularity passed:{self.geo_granularity}, "
        #     f"Possible values are: {GEO_GRANULARITIES}\n"
        # )

    def process(self, target_series, series):
        """Process factor column and obtain level values + filter query.

        If factor-col = provincial then filter for a pre-coded list.
        """
        self.target_series = target_series
        col = self.factor_col
        series = series[target_series]

        if col is not None:
            factor_dtype = series[col].dtype
            factor_levels = series[col].unique()
            logger.debug(
                f"We have these levels ({factor_levels}) on a "{factor_dtype}"-typed col."
            )
            self.factor_levels = factor_levels

        # TODO: Since factor filtering will be done by filter_df factor_query
        # will be have to be removed in a future refactor.
        self.factor_query = f"{col} == @factor_val"

    # def is_national(self):
    #     return self.geo_granularity == NATIONAL_GEO_GRANULARITY

    # def is_provincial(self):
    #     return self.geo_granularity == PROVINCIAL_GEO_GRANULARITY

    def factor_conf_to_pretty_str(self, factor_conf):
        """Format factor configuration to something printable.
        """
        rv = ";".join(f"{k}={v}" for k, v in factor_conf.items())
        return rv

    def factor_conf_to_str(self, factor_conf):
        """Format factor values into a dict.

        The dict returned by this method defines a binary cut on the data based on a set of
        factors. Currently it supports just one.
        """
        # TODO: Enforce key ordering.
        rv = json.dumps(factor_conf)
        return rv

    def filter_df(self, df, factor_val=None):
        """Filter given DataFrame according to factor_val.

        If factor_val is no filtering is performed.
        """
        # if self.is_national() and self.factor_col not in df.columns and factor_val:
        #    # To allow trivial factorization
        #    df[self.factor_col] = factor_val

        if (self.factor_col in df.columns) and factor_val:
            if factor_val not in self.factor_levels:
                raise ValueError(f"{factor_val} isn"t a valid factor level.")
            df = df.query(
                self.factor_query,
                local_dict=dict(factor_val=factor_val),
                global_dict={},
            )
        return df

    def factorize_series(self, series):
        """Generate all posible factorizations of a given series."""
        for factor_val in self.factor_levels:
            rv = SeriesManager()
            for name, df in series.items():
                rv[name] = self.filter_df(df, factor_val)
            factor_conf = {self.factor_col: factor_val}
            yield factor_conf, rv


# def run_series_pipeline(kpi, time_range_conf, extractor, factor_mgr):
def run_series_pipeline(kpi, series_dict, time_range_conf, factor_mgr):
    """Extract and transform a given series."""
    # series_dict = extractor.extract(time_range_conf, kpi.client_type)
    # series_dict = KPISeriesPreprocBase.build_from_kpi(kpi).preproc(series_dict)
    series_mgr = SeriesManager(series_dict)
    # series_mgr.transform(kpi, time_range_conf.time_granularity, factor_mgr)
    # series_mgr.build_regressors()
    factor_mgr.process(kpi.target_series, series_mgr)
    return series_mgr, factor_mgr
