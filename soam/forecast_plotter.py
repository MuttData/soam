# forecast_plotter.py
"""
Forecast Plotter
----------
Postprocess to plot the model forecasts.
"""
import logging
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd

from soam.constants import (DAILY_TIME_GRANULARITY, DS_COL, FORECAST_DATE,
                            PARENT_LOGGER)
from soam.plot_utils import create_forecast_figure
from soam.step import Step
from soam.utils import get_file_path

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


class ForecastPlotter:
    def __init__(self, path: Union[Path, str], metric_name: str):
        """
        Formats and plots the forecaster passed as a parameter.

        Parameters
        ----------
        path : str or pathlib.Path
            Where the plots will be stored.
        metric_name : str
            The name for the metric that its going to plot.
        """

        self.path = Path(path)
        self.metric_name = metric_name

    def plot(self, time_series: pd.DataFrame, predictions: pd.DataFrame,
             time_granularity: str = DAILY_TIME_GRANULARITY) -> Path:
        """
        Create and store the result plot in the constructed path.

        If the path does not exist, it will be created.

        Parameters
        ----------
        time_series
            Dataframe belonging to a time_series of data.
        predictions
            Dataframe with the result of the predictions.
        time_granularity
            Time granularity of the series (daily or hourly)

        Returns
        -------
        pathlib.Path
            The path of the resulting plot
        """
        predictions[DS_COL] = predictions[FORECAST_DATE]

        full_series = pd.concat([predictions, time_series])
        full_series = full_series.drop(columns=[FORECAST_DATE])
        full_series[DS_COL] = pd.to_datetime(full_series[DS_COL])
        start_date = min(pd.to_datetime(time_series[DS_COL]))
        end_date = max(pd.to_datetime(time_series[DS_COL]))

        fig = create_forecast_figure(
            full_series,
            self.metric_name,
            end_date,
            len(predictions),
            time_granularity=time_granularity,
        )

        self.path.mkdir(parents=True, exist_ok=True)
        fn = "_".join(["forecast", f"{start_date:%Y%m%d%H}",
                       f"{end_date:%Y%m%d%H}", ".png"])
        plot_path = get_file_path(self.path, fn)
        logger.debug(f"Saving forecast figure to {plot_path}...")
        fig.savefig(plot_path, bbox_inches="tight")
        return plot_path


class ForecastPlotterTask(Step, ForecastPlotter):
    def __init__(
        self, path: Union[Path, str], metric_name: str, **kwargs: Any,
    ):
        Step.__init__(self, **kwargs)  # type: ignore
        ForecastPlotter.__init__(self, path, metric_name)

    def run(  # type: ignore
        self,
        time_series: pd.DataFrame,
        predictions: pd.DataFrame,
        time_granularity: Optional[str] = DAILY_TIME_GRANULARITY,
    ) -> Path:
        return self.plot(time_series, predictions, time_granularity)
