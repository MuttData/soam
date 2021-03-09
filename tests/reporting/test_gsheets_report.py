from json.decoder import JSONDecodeError
import logging
from unittest.mock import patch

import pandas as pd
import pytest

from soam.reporting import GSheetsReportTask


def test_init_fails_if_config_path_is_not_file():
    with pytest.raises(ValueError, match=r".*[Cc]onfig\Wpath.*"):
        GSheetsReportTask("/not_a_real_file.json")


def test_init_fails_if_config_path_is_not_json(tmp_path):
    test_file = tmp_path / f"gsheets_config.json"
    test_file.write_text("Test text - not json.")
    with pytest.raises(JSONDecodeError):
        GSheetsReportTask(test_file)


def test_run_empty_dataframe_warning(tmp_path, caplog):
    test_file = tmp_path / f"gsheets_config.json"
    test_file.write_text("{}")
    with patch(
        "soam.reporting.gsheets_report.GSheetsClient"
    ) as cli_mock, caplog.at_level(logging.WARNING):
        reporter = GSheetsReportTask(test_file)
        df = pd.DataFrame()
        spreadsheet = "example_spreadsheet"
        reporter.run(df, spreadsheet)
        cli_mock.return_value.insert_from_frame.assert_called_once_with(df, spreadsheet)
        assert "empty dataframe" in caplog.text.lower()
