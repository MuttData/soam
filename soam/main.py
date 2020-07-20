import logging

from soam.cfg import FIG_DIR
from soam.constants import PARENT_LOGGER
from soam.dbconn import PgClient
from soam.forecast_plotter import ForecastPlotter
from soam.forecaster import Forecaster, run_forecaster_pipeline
from soam.helpers import TimeRangeConfiguration
from soam.kpi import KPI
from soam.mail_report import MailReport
from soam.series import FactorManager, run_series_pipeline
from soam.utils import make_dirs

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


def main(
    series_dict,
    factor_col,
    granularity,
    kpi_dict,
    time_range_dict,
    db_creds,
    smtp_creds,
    mail_recipients,
    extra_info=None,
    email_attachments=None,
    store_results=False,
    slack_settings=None,
):

    kpi = KPI(
        target_series=kpi_dict["target_series"],
        target_col=kpi_dict["target_col"],
        name=kpi_dict["name"],
        anomaly_plot_ylabel=kpi_dict["anomaly_plot_ylabel"],
        mail_kpi=kpi_dict["mail_kpi"],
        name_spanish=kpi_dict["name_spanish"],
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
    db_cli_d = dict()
    if store_results:
        db_cli_d = {
            'postgres': PgClient(
                username=db_creds['user'],
                database=db_creds['dbname'],
                host=db_creds['host'],
                dialect='postgres',
                port=5432,
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
            factor_mgr,
            time_range_conf,
            ','.join(all_forecaster_run_ids),
            extra_info,
            email_attachments,
            slack_settings,
        )
    else:
        logger.info("Mail report not send")


if __name__ == "__main__":
    main()
