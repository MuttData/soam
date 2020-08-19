# forecast_plotter.py

import logging
from pathlib import Path
from typing import Union

import pandas as pd
from soam.constants import DAILY_TIME_GRANULARITY, DS_COL, FORECAST_DATE, PARENT_LOGGER
from soam.forecaster import Forecaster
from soam.plot_utils import create_forecast_figure
from soam.utils import get_file_path

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


"""
ForecastPlotter
----------
In charge of formatting and plotting the results of a fitted model.
"""


class ForecastPlotter:
    def __init__(self, path: Union[Path, str], metric_name: str):
        """
        Formats and plots the forecaster passed as a parameter.
        
        Parameters
        ----------
        path
            str or pathlib.Path where the plots will be stored.
        """
        self.path = Path(path)
        self.metric_name = metric_name

    def plot(
        self, forecaster: Forecaster, time_granularity: str = DAILY_TIME_GRANULARITY,
    ) -> Path:
        """
        Create and store the result plot in the constructed path.
        
        If the path does not exist, it will be created.

        Parameters
        ----------
        forecaster
            A Forecaster, it needs to already be `fitted` to properly format it.
        time_granularity
            Time granularity of the series (daily or hourly)
        Returns
        -------
        Path
            The path of the resulting plot

        """
        if forecaster.prediction is None:
            logger.error(
                "The Forecaster object hasn't had a prediction, it's required for plotting."
            )

        predictions = forecaster.prediction
        predictions[DS_COL] = predictions[FORECAST_DATE]
        raw_series = forecaster.raw_series

        full_series = pd.concat([predictions, raw_series])
        full_series = full_series.drop(columns=[FORECAST_DATE])
        full_series[DS_COL] = pd.to_datetime(full_series[DS_COL])
        start_date = min(pd.to_datetime(raw_series[DS_COL]))
        end_date = max(pd.to_datetime(raw_series[DS_COL]))

        fig = create_forecast_figure(
            full_series,
            self.metric_name,
            end_date,
            len(predictions),
            time_granularity=time_granularity,
        )

        self.path.mkdir(parents=True, exist_ok=True)
        fn = "_".join(
            ["forecast", f"{start_date:%Y%m%d%H}", f"{end_date:%Y%m%d%H}", ".png"]
        )
        plot_path = get_file_path(self.path, fn)
        logger.debug(f"Saving forecast figure to {plot_path}...")
        fig.savefig(plot_path, bbox_inches="tight")
        return plot_path
