"""PDF Report test."""
from dateutil.parser import parse
import pdftotext
import pytest

from soam.reporting import PDFReportTask


@pytest.fixture(name='one_cell_notebook_template')
def fixture_one_cell_notebook_template(source):
    return f"""
    {{
        "cells": [
        {{
        "cell_type": "code",
        "execution_count": null,
        "id": "likely-newport",
        "metadata": {{}},
        "outputs": [],
        "source": {source}
        }}
        ],
        "metadata": {{
        "kernelspec": {{
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
        }},
        "language_info": {{
        "codemirror_mode": {{
            "name": "ipython",
            "version": 3
        }},
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "name": "python",
        "nbconvert_exporter": "python",
        "pygments_lexer": "ipython3",
        "version": "3.7.9"
        }}
        }},
        "nbformat": 4,
        "nbformat_minor": 5
    }}
    """


def remove_extra_lines_from_first_page(page_text):
    """Function to remove extra lines from the first page."""
    lines = page_text.split("\n")
    print(lines)
    return "\n".join(lines[2:-2])


def test_run_fails_if_path_is_not_file():
    """Function to test if path is file."""
    reporter = PDFReportTask("/not_a_real_file.txt")
    test_path = "test"
    with pytest.raises(ValueError, match=r".*file*"):
        reporter.run(test_path, {})


@pytest.mark.parametrize('source', [[]])
def test_run_empty_notebook(one_cell_notebook_template, tmp_path):
    """Test run empty notebook."""
    base_file_name = 'empty_notebook'
    test_file = tmp_path / f"{base_file_name}.ipynb"
    test_file.write_text(one_cell_notebook_template)
    reporter = PDFReportTask(tmp_path)
    outfile = reporter.run(test_file, {})
    assert base_file_name in outfile
    parse(outfile.split("/")[-1], fuzzy=True)
    with open(outfile, 'rb') as f:
        pdf = pdftotext.PDF(f)
    assert len(pdf) == 1
    assert remove_extra_lines_from_first_page(pdf[0]).strip() == ""


@pytest.mark.parametrize('source', ['''["display(\\"Example\\")"]'''])
def test_run_one_cell_notebook(one_cell_notebook_template, tmp_path):
    """Test run one cell notebook."""
    base_file_name = 'one_cell_notebook'
    test_file = tmp_path / f"{base_file_name}.ipynb"
    test_file.write_text(one_cell_notebook_template)
    reporter = PDFReportTask(tmp_path)
    outfile = reporter.run(test_file, {})
    assert base_file_name in outfile
    parse(outfile.split("/")[-1], fuzzy=True)
    with open(outfile, 'rb') as f:
        pdf = pdftotext.PDF(f)
    assert len(pdf) == 1
    assert remove_extra_lines_from_first_page(pdf[0]).strip() == "'Example'"
