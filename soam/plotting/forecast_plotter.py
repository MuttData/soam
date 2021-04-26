"""
Forecast Plotter
----------------
Postprocess to plot the model forecasts.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from prefect.utilities.tasks import defaults_from_attrs

from soam.constants import DAILY_TIME_GRANULARITY, DS_COL
from soam.core.step import Step
from soam.plotting.plot_utils import create_forecast_figure
from soam.utilities.utils import get_file_path

logger = logging.getLogger(__name__)


class ForecastPlotterTask(Step):
    """
    Plot forecasts.

    Parameters
    ----------
    path : pathlib.Path or str
        Path to which plots will be saved.
    metric_name : str
        Name of the metric to plot.
    time_granularity : str
        Time granularity used on the plot. Defaults to `DAILY_TIME_GRANULARITY`.
    plot_config: dict
        Misc configs passed to `create_forecast_figure`.
    savefig_opts: dict
        kwargs passed to `savefig`.
    """

    def __init__(
        self,
        path: Path,
        metric_name: str,
        time_granularity: str = DAILY_TIME_GRANULARITY,
        plot_config: Optional[Dict] = None,
        savefig_opts: Optional[Dict] = None,
        **kwargs: Any,
    ):
        """
        Forecast plotter initialization

        Parameters
        ----------
            path: Path:
                file path.
            metric_name str:
                performance metric being measured.
            time_granularity: str
                How much a time period accounts for. Defaults is daily time granularity.
            plot_config: dict
                plot configurations, default is None.
            savefig_opts: dict
                saving options, default is None.
        """
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

        path = path or self.path
        self.path.mkdir(parents=True, exist_ok=True)
        fn = "_".join(
            ["forecast", f"{start_date:%Y%m%d%H}", f"{end_date:%Y%m%d%H}", ".png"]
        )
        plot_path = get_file_path(path, fn)
        logger.debug(f"Saving forecast figure to {plot_path}...")
        fig.savefig(plot_path, bbox_inches="tight", **savefig_opts)
        self.fig = fig
        return plot_path
