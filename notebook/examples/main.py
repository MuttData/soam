"""Main module for python notebooks examples"""
import datetime
import logging

from darts import models
from muttlib.dbconn import PgClient
import pandas as pd
from prefect import task

from soam.cfg import get_db_cred
from soam.core import SoamFlow
from soam.plotting.forecast_plotter import ForecastPlotterTask
from soam.reporting.slack_report import SlackReportTask
from soam.savers.db_saver import DBSaver
from soam.savers.csv_saver import CSVSaver
from soam.workflow import Forecaster

logger = logging.getLogger(__name__)

URL = "notebook/data/revenue.csv"
now = datetime.datetime.today()


@task
def read_csv_data(path: str) -> pd.DataFrame:
    """Read data from a csv and output a dataframe"""
    df = pd.read_csv(path)
    df["ds"] = df["date"]
    df = df[df["game"] == "battletanksbeta"]
    df = df.groupby("ds").mean().reset_index()
    df["y"] = df["revenue"]
    df = df.drop(columns=["row_count", "requests", "impressions", "clicks", "revenue"])
    return df


def main(time_series_path: str):
    saver_data = CSVSaver("/tmp/soam_data/")
    db_cred = get_db_cred("soam/settings.ini")
    db = PgClient(**db_cred)
    saver_runs = DBSaver(db)

    my_model = models.Prophet(weekly_seasonality=True, daily_seasonality=False)
    forecaster = Forecaster(my_model, savers=[saver_data])
    forecast_plotter = ForecastPlotterTask(".", "Retail Sales")
    slack_report = SlackReportTask("C01AB7A2HG9", "revenue", "soam/settings.ini")

    with SoamFlow(name="main_test", saver=saver_runs) as f:
        f.start_datetime = now
        f.end_datetime = now

        df = read_csv_data(path=time_series_path)
        preds_model = forecaster(time_series=df, output_length=7)
        plot_fn = forecast_plotter(preds_model[1], preds_model[0])
        slack_report(preds_model[0], plot_fn)

    f.run()


if __name__ == "__main__":
    main(URL)
