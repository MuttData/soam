"""Analyze time series data based on company KPIs."""
import logging
from functools import partial

import numpy as np
import pandas as pd
from fbprophet import Prophet

import helpers
from helpers import get_figure_full_path, AbstractAnalisysRun
from utils import normalize_ds_index, apply_time_bounds

from cfg import FIG_DIR

from constants import (
    DEFAULT_PROPHET_ARGS,
    DS_COL,
    HOURLY_TIME_GRANULARITY,
    PARENT_LOGGER,
    Y_COL,
)
from data_models import ForecasterRuns, ForecasterValues

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")

FORECAST_DATE_COL = "forecast_date"
FLOOR_COL = "floor"
CAP_COL = "cap"
DAY_NAME = "day_name"
YHAT_LOWER_COL = "yhat_lower"
YHAT_UPPER_COL = "yhat_upper"
YHAT_COL = "yhat"
TREND_COL = "trend"
OUTLIER_VALUE_COL = "outlier_value"
OUTLIER_SIGN_COL = "outlier_sign"

INPUT_PROPHET_COLS = [DS_COL, Y_COL, DAY_NAME]
OUTPUT_PROPHET_COLS = [
    DS_COL,
    YHAT_LOWER_COL,
    YHAT_UPPER_COL,
    Y_COL,
    YHAT_COL,
    TREND_COL,
]
OUTPUT_FORECASTER_COLS = [
    FORECAST_DATE_COL,
    YHAT_LOWER_COL,
    YHAT_UPPER_COL,
    Y_COL,
    YHAT_COL,
    TREND_COL,
    OUTLIER_VALUE_COL,
    OUTLIER_SIGN_COL,
]

# To be deprecated:
forecasts_fig_path = partial(get_figure_full_path, fig_dir=FIG_DIR, fig_name="forecast")


def _process_caps(max_cap, min_floor, ratio_correction):
    """Process passed caps based on granularities."""
    if max_cap is not None:
        max_cap = max_cap / ratio_correction
    if min_floor is not None:
        min_floor = min_floor / ratio_correction
    return max_cap, min_floor


def _log_transform_data(data, cols=None):
    """Transform columns previous to model fitting."""
    if cols:  # only non-empty case
        logger.info(f"Log transforming + 1, the following cols: {cols}.")
        data[cols] = pd.np.log(data[cols] + 1)
    elif cols is None:
        cols = [Y_COL]
    return data


def compute_mape(y_true, y_hat):
    return np.mean(np.abs((y_true - y_hat) / y_true)) * 100


def _exp_transform_data(data, cols=None):
    """Transform columns after model fit."""
    if cols is None:
        cols = [Y_COL]
    logger.info(f"Exp -1 un-transforming, the following cols: {cols}.")
    data[cols] = pd.np.exp(data[cols]) - 1
    # Ensure we don't actually have any value below 0
    data[cols] = data[cols].clip(lower=0)
    return data


def _add_day_name(df):
    """Add a column of dayname from a datestamp column."""
    df[DAY_NAME] = df[DS_COL].dt.day_name()
    return df


class Forecaster(AbstractAnalisysRun):
    """Class to build forecasts and detect anomalies in a timeseries."""

    db_run_class = ForecasterRuns
    db_value_class = ForecasterValues

    def __init__(
        self,
        max_cap,
        min_floor,
        ratio_correction=1,
        time_multiplier=1,
        base_model_kws=None,
        metric_non_negative=False,
        known_outlier_dates=None,
    ):
        """Initialize MetricSeries object.

        Args:
            series (pd.DataFrame): Dataframe with one columna for the time index named
                DS_COL and another column for the values named Y_COL.
            start_date (datetime): Start of the data to train
            end_date (datetime): End of the data to train,
            future_date (datetime): Prediction end date,
            max_cap (float): Upper bond for series values
            min_floor (float): Lower bond for series values
        """
        self.metric_non_negative = metric_non_negative
        self.max_cap, self.min_floor = _process_caps(
            max_cap, min_floor, ratio_correction
        )
        self.time_multiplier = time_multiplier

        if base_model_kws is None:
            base_model_kws = {}
        self.base_model_kws = base_model_kws

        self._fbprophet_model = None
        self._fitted_model = None
        self.forecast = None

        self.input_cols = INPUT_PROPHET_COLS.copy()
        if self.min_floor:
            self.input_cols.append(FLOOR_COL)
        if self.max_cap:
            self.input_cols.append(CAP_COL)

        if known_outlier_dates is None:
            known_outlier_dates = []
        self.known_outlier_dates = known_outlier_dates

    def get_children_data(self):
        return self.forecast.rename(columns={DS_COL: FORECAST_DATE_COL})[
            OUTPUT_FORECASTER_COLS
        ].copy()

    def get_empty_forecast(self, time_range_conf):
        """Init a new future series with appropriate reggressors."""
        fc = (
            pd.date_range(
                start=time_range_conf.start_date,
                end=time_range_conf.future_date,
                freq=time_range_conf.time_granularity,
            )
            .to_frame()
            .rename(columns={0: DS_COL})
        )
        fc = self._define_data_bounds(fc)
        return fc

    def _define_data_bounds(self, df):
        """Process passed caps based on time granularity."""
        if self.min_floor is not None:
            df[FLOOR_COL] = self.min_floor / self.time_multiplier
        if self.max_cap is not None:
            df[CAP_COL] = self.max_cap / self.time_multiplier
        return df

    def check_series(self, series, min_series_len=10):
        """Check if the series has enough data to work."""
        return series.shape[0] > min_series_len

    # def prepare_series(self, kpi, time_range_conf, series):
    def prepare_series(self, time_range_conf, series):
        """
        Get data from a pandas DataFrame with correct columns and values.

        Also set the class attribute to a clean new kpi series.
        """
        series = normalize_ds_index(series, DS_COL)

        series = series[[DS_COL, Y_COL]].copy()
        series[DS_COL] = pd.to_datetime(series[DS_COL])
        series = _add_day_name(series)
        series = self._define_data_bounds(series)
        series = apply_time_bounds(
            df=series,
            sd=time_range_conf.start_date,
            ed=time_range_conf.end_date,
            ds_col=DS_COL,
        )
        series = series[self.input_cols]

        if self.known_outlier_dates:
            series.loc[series[DS_COL].isin(self.known_outlier_dates), "y"] = None
        return series

    def add_regressor(self, series, fc, reg_df, rname, col):
        """Add a column to series/forecast with regressor data.

        It will add the regressor column using the prefix for regressors +
        the name passed to this method.
        """
        # Convert column to new names for better filtering suffix
        reg_df.rename(columns={col: rname}, inplace=True)

        # Merge data and fill if necessary when nulls are present
        series = pd.merge(series, reg_df, on=DS_COL, how="left").fillna(0)
        fc = pd.merge(fc, reg_df, on=DS_COL, how="left").fillna(0)
        return series, fc

    def build_model(self, series, fc, regressors_list, time_range_conf):
        """Load regressors from list of regressor objects."""
        holidays_regs = [r for r in regressors_list if r.is_holiday]
        non_holidays_regs = [r for r in regressors_list if not r.is_holiday]

        model_kws = self.base_model_kws.copy()

        interval_width = model_kws.get(
            "interval_width", DEFAULT_PROPHET_ARGS["interval_width"]
        )
        if time_range_conf.time_granularity == HOURLY_TIME_GRANULARITY:
            interval_width /= 0.9
        model_kws["interval_width"] = interval_width

        monthly_seasonality = False
        if "monthly_seasonality" in model_kws:
            monthly_seasonality = model_kws.pop("monthly_seasonality")

        if holidays_regs:
            # Bump fbprophet model kws with holiday args
            if len(holidays_regs) > 1:
                logger.warning(
                    "The prior_scale of the first holiday is considered for all of them."
                )

            prior_scale = holidays_regs[0].prior_scale
            df_hrs = pd.concat([hr.df for hr in holidays_regs])
            model_kws.update(holidays=df_hrs, holidays_prior_scale=prior_scale)

        # We need a new model previous to adding regressors
        self._fbprophet_model = Prophet(**{**DEFAULT_PROPHET_ARGS, **model_kws})

        if monthly_seasonality:
            # TODO: This should be an external conf instead of a hardcoded value.
            # Note: we use fourier order 10 to allow seasonality to change quickly
            self._fbprophet_model.add_seasonality(
                name="monthly", period=30.5, fourier_order=10
            )

        for reg in non_holidays_regs:
            series, fc = self.add_regressor(series, fc, reg.df, reg.name, col=reg.col)
            # Fbprophet needs to map regressor names with cols
            self._fbprophet_model.add_regressor(reg.col, prior_scale=reg.prior_scale)

        return series, fc

    def _check_add_cap_floor_cols(self, cols=None):
        """Check if model uses floor/cap cols and add them to col list."""
        if cols is None:
            cols = [Y_COL]
        rv = cols.copy()
        if self.max_cap:
            rv.append(CAP_COL)
        if self.min_floor:
            rv.append(FLOOR_COL)
        return rv

    def fit(self, series):
        """Fit the Prophet model.

        This sets self.params to contain the fitted model parameters. It is a
        dictionary parameter names as keys and the following items:
            k (Mx1 array): M posterior samples of the initial slope.
            m (Mx1 array): The initial intercept.
            delta (MxN array): The slope change at each of N changepoints.
            beta (MxK matrix): Coefficients for K seasonality features.
            sigma_obs (Mx1 array): Noise level.
        Note that M=1 if MAP estimation.

        Parameters
        ----------
        df: pd.DataFrame containing the history. Must have columns ds (date
            type) and y, the time series. If self.growth is 'logistic', then
            df must also have a column cap that specifies the capacity at
            each ds.
        kwargs: Additional arguments passed to the optimizing or sampling
            functions in Stan.

        Returns
        -------
        The fitted Prophet object

        """
        vals = series.copy()
        if self.metric_non_negative:
            logger.debug(
                f"Non-negative metric flag is set to '{self.metric_non_negative}'. "
                "Will proceed map data into log-space for fitting."
            )
            log_cols = self._check_add_cap_floor_cols()
            vals = _log_transform_data(vals, log_cols)
        self._fitted_model = self._fbprophet_model.fit(vals)

    def predict(self, series, fc):
        """Predict using the prophet model.

        It will plot it on the internally set forecast
        ----------
        df: pd.DataFrame with dates for predictions (column ds), and capacity
            (column cap) if logistic growth. If not provided, predictions are
            made on the history.

        Returns
        -------
        A pd.DataFrame with the forecast components.

        """
        # TODO: Find a way to silence fitting messages
        if self.metric_non_negative:
            # log transform cols fit prophet
            log_cols = self._check_add_cap_floor_cols(
                cols=[]
            )  # no y col in forecast yet
            fc = _log_transform_data(fc, log_cols)

        fc = self._fitted_model.predict(fc)

        # To debug fitted model
        # fig = self._fitted_model.plot(fc)
        # fig.savefig('foo.png')

        # Needs real values of historical data for plots
        fc = pd.merge(fc, series[[DS_COL, Y_COL]], on=DS_COL, how="left")
        if self.metric_non_negative:
            # exp transform forecasted hat cols, trend
            exp_cols = [v for v in OUTPUT_PROPHET_COLS if v not in [DS_COL, Y_COL]]
            exp_cols = list(set(log_cols + exp_cols))
            fc = _exp_transform_data(fc, exp_cols)

        mape = compute_mape(fc.y, fc.yhat)
        logger.debug(f"Mape: {mape}%")

        return fc

    def calculate_outliers(self, fc, inplace=False):
        """Calculate outliers from the historical vs. fit differences."""
        if not inplace:
            fc = fc.copy()
        fc[OUTLIER_SIGN_COL] = fc.eval(f"y > {YHAT_UPPER_COL}").astype(int)  # positive
        fc[OUTLIER_SIGN_COL] -= fc.eval(f"y < {YHAT_LOWER_COL}").astype(int)  # negative
        fx = fc.ds.min()
        # Filter outliers only
        fc = fc.query(f"{DS_COL} >= @fx", global_dict={}, local_dict=dict(fx=fx))

        def calculate_outlier_value(row):
            if row.outlier_sign < 0:
                value = row.yhat_lower - row.y

            elif row.outlier_sign > 0:
                value = row.y - row.yhat_upper
            else:
                # Not an outlier, return 0
                value = 0

            return value

        fc[OUTLIER_VALUE_COL] = fc.apply(calculate_outlier_value, axis=1)
        return fc

    @property
    def outlier_dates(self):
        df = self.forecast
        df = df.loc[df[OUTLIER_SIGN_COL] != 0, DS_COL]
        return df

    # def run(self, kpi, time_range_conf, raw_series, regressors_l):
    def run(self, time_range_conf, raw_series, regressors_l):
        """Compute Metric's main subroutine."""
        logger.info("Running subroutine to identify outliers....")
        if self.check_series(raw_series):
            logger.info(f"Running forecaster...")
            # series = self.prepare_series(kpi, time_range_conf, raw_series)
            series = self.prepare_series(time_range_conf, raw_series)
            forecast_empty = self.get_empty_forecast(time_range_conf)
            series_with_regs, forecast_with_regs = self.build_model(
                series, forecast_empty, regressors_l, time_range_conf
            )
            self.fit(series_with_regs)
            forecast_preds = self.predict(series_with_regs, forecast_with_regs)
            forecast_final = self.calculate_outliers(forecast_preds)
            # Replace null y's with -1 to avoid having nulls in dbs
            # FIXME: Is better to use `df.where(df.notnull(), None)` but we still have null constraint
            forecast_final[Y_COL].replace(np.nan, -1, inplace=True)
        else:
            logger.error(f"Target series is empty or too small for this")
            forecast_final = None

        self.forecast = forecast_final
        return self.forecast


def run_forecaster_pipeline(
    kpi,
    time_range_conf,
    series_mgr,
    forecaster,
    forecaster_plotter=None,
    db_cli_d=dict(),
):
    forecaster.run(
        time_range_conf,
        raw_series=series_mgr[kpi.target_series].rename(
            columns={kpi.target_col: Y_COL}
        ),
        regressors_l=series_mgr.regressors_l,  # We could use placements here or other metrics here.
    )
    run_ids = forecaster.save(db_cli_d)
    if forecaster_plotter:
        forecaster_plotter.plot(
            forecaster, time_range_conf, kpi.name, kpi.anomaly_plot_ylabel, kpi.mail_kpi
        )
    return forecaster, run_ids
