# forecast_plotter.py
"""
Forecast Plotter
----------
Postprocess to plot the model forecasts.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pandas as pd
from prefect.utilities.tasks import defaults_from_attrs

from soam.constants import DAILY_TIME_GRANULARITY, DS_COL, PARENT_LOGGER
from soam.plot_utils import create_forecast_figure
from soam.step import Step
from soam.utils import get_file_path

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


class ForecastPlotterTask(Step):
    def __init__(
        self,
        path: Union[Path, str],
        metric_name: str,
        time_granularity: str = DAILY_TIME_GRANULARITY,
        plot_config: Optional[Dict] = None,
        savefig_opts: Optional[Dict] = None,
        **kwargs: Any,
    ):
        Step.__init__(self, **kwargs)  # type: ignore
        self.path = path
        self.metric_name = metric_name
        self.time_granularity = time_granularity
        self.plot_config = plot_config
        if savefig_opts is None:
            savefig_opts = {}
        self.savefig_opts = savefig_opts

        # Last image rendered. Used for testing.
        self.fig = None

    @defaults_from_attrs(
        'path', 'metric_name', 'time_granularity', 'plot_config', 'savefig_opts'
    )
    def run(  # type: ignore
        self,
        time_series: pd.DataFrame,
        predictions: pd.DataFrame,
        path=None,
        metric_name=None,
        time_granularity=None,
        plot_config=None,
        savefig_opts=None,
    ) -> Path:
        """
        Create and store the result plot in the constructed path.

        If the path does not exist, it will be created.

        Parameters
        ----------
        time_series
            Dataframe belonging to a time_series of data.
        predictions
            Dataframe with the result of the predictions.

        Returns
        -------
        pathlib.Path
            The path of the resulting plot
        """

        full_series = pd.concat([predictions, time_series])
        full_series[DS_COL] = pd.to_datetime(full_series[DS_COL])
        start_date = min(pd.to_datetime(time_series[DS_COL]))
        end_date = pd.to_datetime(predictions[DS_COL]).min()

        forecast_window = (pd.to_datetime(predictions[DS_COL]).max() - end_date).days

        fig = create_forecast_figure(
            full_series,
            metric_name,
            end_date,
            forecast_window,
            time_granularity=time_granularity,
            plot_config=plot_config,
        )

        path.mkdir(parents=True, exist_ok=True)
        fn = "_".join(
            ["forecast", f"{start_date:%Y%m%d%H}", f"{end_date:%Y%m%d%H}", ".png"]
        )
        plot_path = get_file_path(path, fn)
        logger.debug(f"Saving forecast figure to {plot_path}...")
        fig.savefig(plot_path, bbox_inches="tight", **savefig_opts)
        self.fig = fig
        return plot_path
