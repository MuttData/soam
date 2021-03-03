from unittest.mock import patch

import pytest

from soam.reporting import IpynbToPDF


def test_run_fails_if_path_is_not_file():
    with patch("soam.reporting.pdf_report.Path") as path_mock:
        path_mock.return_value.is_file.return_value = False
        reporter = IpynbToPDF("base_path")
        with pytest.raises(ValueError, match=r".*file*"):
            reporter.run("test_in", {})
