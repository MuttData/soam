import logging

from soam.cfg import FIG_DIR
from soam.constants import PARENT_LOGGER
from soam.forecast_plotter import ForecastPlotter
from soam.forecaster import Forecaster, run_forecaster_pipeline
from soam.mail_report import MailReport
from soam.series import run_series_pipeline, FactorManager
from soam.utils import make_dirs
from soam.helpers import TimeRangeConfiguration
from soam.dbconn import PgClient

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


def main(
    series_dict,
    factor_col,
    granularity,
    time_range_dict,
    db_creds,
    smtp_creds,
    mail_recipients,
):
    class KPI:
        def __init__(
            self,
            target_series,
            target_col,
            name,
            anomaly_plot_ylabel,
            mail_kpi,
            name_spanish,
        ):
            self.target_series = target_series
            self.target_col = target_col
            self.name = name
            self.anomaly_plot_ylabel = anomaly_plot_ylabel
            self.mail_kpi = mail_kpi
            self.name_spanish = name_spanish

    kpi = KPI(
        target_series="cache_successes",
        target_col="cache_successes",
        name="cache_success",
        anomaly_plot_ylabel="cache_success",
        mail_kpi="cache_success",
        name_spanish="cache_success",
    )
    time_range_conf = TimeRangeConfiguration(
        end_date=time_range_dict['end_date'],
        forecast_train_window=time_range_dict['train_window'],
        forecast_future_window=time_range_dict['future_window'],
        time_granularity=time_range_dict['time_granularity'],
        anomaly_window=time_range_dict['anomaly_window'],
        end_hour=time_range_dict['end_hour'],
    )

    # DB client setup
    db_cli_d = {
        'postgres': PgClient(
            username=db_creds['user'],
            database=db_creds['dbname'],
            host=db_creds['host'],
            dialect='postgres',
            port=5432,
            # driver=,
            password=db_creds['password'],
        ),
    }

    factor_mgr = FactorManager(factor_col=factor_col)
    forecaster = Forecaster(min_floor=None, max_cap=None)
    mail_reporter = MailReport(mail_recipients, smtp_creds)

    series_mgr, factor_mgr = run_series_pipeline(
        kpi, series_dict, time_range_conf, factor_mgr
    )
    base_fig_dir = make_dirs(FIG_DIR / granularity / time_range_conf.time_granularity)

    all_forecaster_run_ids = []

    for factor_conf, series_mgr_cut in factor_mgr.factorize_series(series_mgr):
        factor_conf_pretty = factor_mgr.factor_conf_to_pretty_str(factor_conf)
        logger.info(f"Running pipeline for factor: `{factor_conf_pretty}`")
        series_mgr, factor_mgr = run_series_pipeline(
            kpi, series_dict, time_range_conf, factor_mgr
        )

        logger.info(f"Running forecast pipeline")

        forecaster_plotter = ForecastPlotter(
            factor_val=factor_conf[factor_mgr.factor_col],
            save_suffix=factor_conf_pretty,
            save_path=base_fig_dir,
        )

        forecaster, forecaster_run_ids = run_forecaster_pipeline(
            kpi,
            time_range_conf,
            series_mgr_cut,
            forecaster,
            forecaster_plotter=forecaster_plotter,
            db_cli_d=db_cli_d,
        )
        mail_reporter.store_forecast_data(forecaster, factor_conf, factor_mgr)

    if mail_reporter:
        logger.info("Sending mail report")
        mail_reporter.send(
            kpi,
            granularity,
            time_range_conf,
            factor_mgr,
            ','.join(all_forecaster_run_ids),
            series_dict['cache_successes'],
        )
    else:
        logger.info("Mail report not send")


if __name__ == "__main__":
    main()
