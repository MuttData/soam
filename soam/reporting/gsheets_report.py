import logging
from pathlib import Path
from typing import Mapping

from muttlib.gsheetsconn import GSheetsClient
import pandas as pd

from soam.core import Step

logger = logging.getLogger(__name__)


class GSheetsReportTask(Step):
    """Task to report to GSheets spreadsheet
    """

    def __init__(
        self, config_json_path: str, gsheets_kwargs: Mapping = None, **kwargs
    ):  # pylint: disable=dangerous-default-value
        """Parameters
        ----------
        config_json_path: str
            Path to GSheets config json
        gsheets_kwargs: dict
            Extra args to pass to muttlib.gsheetsconn.GSheetsClient
        kwargs:
            Extra args to pass to soam.core.Step
        """
        Step.__init__(self, **kwargs)  # type: ignore
        config_path = Path(config_json_path)
        if not config_path.is_file():
            raise ValueError("Config path does not point to a file.")
        if not gsheets_kwargs:
            gsheets_kwargs = {}
        self.client = GSheetsClient(config_path, **gsheets_kwargs)

    def run(self, df: pd.DataFrame, spreadsheet: str, **insert_kwargs):
        """Save df to a GSheets spreadsheet

        Parameters
        ----------
        df: pd.DataFrame
            A pandas DataFrame containing the data for the step
        spreadsheet: str
            Spreadsheet id or name as in Drive.
        kwargs:
            Extra args to pass to muttlib.gsheetsconn.GSheetsClient.insert_from_frame
        """

        if df.empty:
            logger.warning("Exporting empty DataFrame")

        return self.client.insert_from_frame(df, spreadsheet, **insert_kwargs)
