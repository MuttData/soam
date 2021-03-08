import pytest

from soam.reporting import GSheetsReportTask


def test_init_fails_if_config_path_is_not_file():
    with pytest.raises(ValueError, match=r".*[Cc]onfig\Wpath.*"):
        GSheetsReportTask("/not_a_real_file.json")
