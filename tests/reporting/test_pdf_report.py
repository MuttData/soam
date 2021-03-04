from unittest.mock import patch

from PyPDF2 import PdfFileReader
from dateutil.parser import parse
import pytest

from soam.reporting import IpynbToPDF


@pytest.fixture(name='empty_notebook_template')
def fixture_empty_notebook_template():
    return """
    {
        "cells": [
        {
        "cell_type": "code",
        "execution_count": null,
        "id": "likely-newport",
        "metadata": {},
        "outputs": [],
        "source": []
        }
        ],
        "metadata": {
        "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
        },
        "language_info": {
        "codemirror_mode": {
            "name": "ipython",
            "version": 3
        },
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "name": "python",
        "nbconvert_exporter": "python",
        "pygments_lexer": "ipython3",
        "version": "3.7.9"
        }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    """


def test_run_fails_if_path_is_not_file():
    with patch("soam.reporting.pdf_report.Path") as path_mock:
        path_mock.return_value.is_file.return_value = False
        reporter = IpynbToPDF("base_path")
        test_path = "test"
        with pytest.raises(ValueError, match=r".*file*"):
            reporter.run(test_path, {})
        path_mock.assert_called_with(test_path)


def test_run_empty_notebook(empty_notebook_template, tmp_path):
    base_file_name = 'empty_notebook'
    test_file = tmp_path / f"{base_file_name}.ipynb"
    test_file.write_text(empty_notebook_template)
    reporter = IpynbToPDF(tmp_path)
    outfile = reporter.run(test_file, {})
    assert base_file_name in outfile
    parse(outfile.split("/")[-1], fuzzy=True)
    pdf = PdfFileReader(outfile)
    assert pdf.getNumPages() == 1
    assert pdf.getPage(0).extractText().strip() == ""
