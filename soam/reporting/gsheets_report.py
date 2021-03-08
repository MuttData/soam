from pathlib import Path

from muttlib.gsheetsconn import GSheetsClient

from soam.core import Step


class TimeSeriesToGSheets:
    """Export time_series data to GSheets."""

    def __init__(self, config_json_path: str, **kwargs):
        """Merge on concat dataframes dependending on the keys.

        Parameters
        ----------
        config_json_path:
            str with the path to Google Sheets secrets json.
        """
        config_path = Path(config_json_path)

        if not config_path.is_file():
            raise ValueError("Config path does not point to a file.")

        self.client = GSheetsClient(config_path, **kwargs)


class GSheetsReportTask(Step, TimeSeriesToGSheets):
    def __init__(
        self, config_json_path: str, gsheets_kwargs: dict = {}, **kwargs
    ):  # pylint: disable=dangerous-default-value
        Step.__init__(self, **kwargs)  # type: ignore
        TimeSeriesToGSheets.__init__(self, config_json_path, **gsheets_kwargs)

    def run(self):
        raise NotImplementedError
