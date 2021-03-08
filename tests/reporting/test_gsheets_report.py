from json.decoder import JSONDecodeError

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
