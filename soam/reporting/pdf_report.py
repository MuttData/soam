"""PDF Generator."""
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict

import jupytext
from nbconvert import PDFExporter
import pandas as pd
import papermill as pm
from pkg_resources import resource_filename

from soam.core import Step

logger = logging.getLogger(__name__)


class PDFReport:
    """Generate PDF from IPython Notebook."""

    def __init__(self, base_path: str):
        """Merge on concat dataframes dependending on the keys.

        Parameters
        ----------
        keys:
            str or list of str labels of columns to merge on
        """
        self.base_path = Path(base_path)

    def export_notebook_to_pdf(self, nb_path: str, nb_params: Dict) -> str:  # type: ignore
        """Run notebook, convert, save and return PDF path.

        Parameters
        ----------
        nb_path : str
            Path of the Notebook or Script to Execute .ipynb / .py
        parameters : Dict
            Parameters to run the notebook with (Papermill).

        Returns
        -------
        str
            Generated PDF Path
        """
        report_file = Path(nb_path)

        if not report_file.is_file():
            raise ValueError("Notebook path does not point to a file.")

        nb_params = self._parse_params(nb_params)

        report_filename, report_extension = report_file.stem, report_file.suffix

        if report_extension != "ipynb":
            report_nb = self.base_path / f"{report_filename}.ipynb"
        else:
            report_nb = report_file

        now_timestamp = datetime.today().strftime('%Y-%m-%dT%H-%M-%S')

        run_nb = self.base_path / f"{report_filename} {now_timestamp}.ipynb"
        pdf_filename = self.base_path / f"{report_filename} {now_timestamp}.pdf"

        logger.info("Running %s and converting to %s", run_nb, pdf_filename)

        jupytext_notebook = jupytext.read(report_file)
        # write to execution nb
        jupytext.write(jupytext_notebook, report_nb)

        _ = pm.execute_notebook(str(report_nb), str(run_nb), parameters=nb_params,)

        pdfexp = PDFExporter(
            template_file=resource_filename("soam", "resources/pdf_report.tpl")
        )

        pdf_data, _ = pdfexp.from_filename(run_nb)

        with open(pdf_filename, "wb") as f:
            f.write(pdf_data)

        logger.info("Succesfully wrote: %s", str(pdf_filename))

        return str(pdf_filename)

    def _parse_params(self, nb_params):
        """Convert common object types to appropiate parameter types."""
        for key, value in nb_params.items():
            if isinstance(value, pd.DataFrame):
                nb_params[key] = value.to_csv(index=False)
        return nb_params


class PDFReportTask(Step, PDFReport):
    def __init__(self, base_path: str):
        Step.__init__(self)
        PDFReport.__init__(self, base_path)

    def run(self, nb_path: str, nb_params: Dict) -> str:  # type: ignore[override]
        return self.export_notebook_to_pdf(nb_path, nb_params)
