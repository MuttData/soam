# forecaster.py
"""
Preprocessor
----------
"""

from typing import TYPE_CHECKING, List, Optional, Tuple  # pylint:disable=unused-import

import pandas as pd
from prefect.utilities.tasks import defaults_from_attrs

from soam.helpers import BaseDataFrameTransformer
from soam.step import Step

if TYPE_CHECKING:
    from soam.savers import Saver


class Preprocessor(Step):
    def __init__(
        self, preprocessor: BaseDataFrameTransformer, savers: "Optional[List[Saver]]", **kwargs
    ):
        """Handle transformations

        Parameters
        ----------
        preprocessor: BaseDataFrameTransformer
            Object that implements transformations a given dataset.
        savers : list of soam.savers.Saver, optional
            The saver to store the parameters and state changes.
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:
                self.state_handlers.append(saver.save_forecast)

        self.preprocessor = preprocessor

    @defaults_from_attrs
    def run(  # type: ignore
        self, 
        dataset: pd.DataFrame,
        **kwargs
    ) -> Tuple[pd.DataFrame, BaseDataFrameTransformer]:
        """
        Run a preprocessor on ,
        creating a TimeSeries from a pandas DataFrame
        and storing the prediction with in the object.

        Parameters
        ----------
        dataset : pandas.DataFrame
            Dataset with data to be processed.

        Returns
        -------
        tuple of (pandas.DataFrame, BaseDataFrameTransformer)
            A tuple containing a pandas DataFrame with the predicted values
            and the fitted preprocessor.
        """
        self.dataset = dataset.copy()
        self.transformed_data = self.preprocessor.fit_transform()
        return transformed_data, self.preprocessor
