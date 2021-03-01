# transformer.py
"""
Transformer
-----------
"""

import logging
from typing import TYPE_CHECKING, List, Optional, Tuple  # pylint:disable=unused-import

import pandas as pd
from prefect.utilities.tasks import defaults_from_attrs
from sklearn.base import BaseEstimator, TransformerMixin

from soam.core import Step

if TYPE_CHECKING:
    from soam.savers import Saver


logger = logging.getLogger(__name__)


class BaseDataFrameTransformer(BaseEstimator, TransformerMixin):
    """Provide an interface to transform pandas DataFrames."""

    def fit(
        self, X: pd.DataFrame, **fit_params  # pylint:disable=unused-argument
    ) -> "BaseDataFrameTransformer":
        """This fits the transformer to the passed data."""
        logger.warning("Subclasses should implement this.")
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError("Subclasses should implement this.")

    def fit_transform(self, X: pd.DataFrame, **fit_params) -> pd.DataFrame:
        return self.fit(X, **fit_params).transform(X)


class DummyDataFrameTransformer(BaseDataFrameTransformer):
    def __init__(self):
        pass

    def fit(self, df_X):  # pylint:disable=unused-argument
        return self

    def transform(self, df_X, inplace=True):
        if not inplace:
            df_X = df_X.copy()
        return df_X


class Transformer(Step):
    transformer: BaseDataFrameTransformer

    def __init__(
        self,
        transformer: BaseDataFrameTransformer = None,
        savers: "Optional[List[Saver]]" = None,
        **kwargs
    ):
        """Handle transformations

        Parameters
        ----------
        transformer: BaseDataFrameTransformer
            Object that implements transformations a given dataset.
        savers : list of soam.savers.Saver, optional
            The saver to store the parameters and state changes.
        """
        super().__init__(**kwargs)
        if savers is not None:
            for saver in savers:
                self.state_handlers.append(saver.save_forecast)

        self.dataset = None
        self.transformed_dataset = None

        if transformer is None:
            transformer = DummyDataFrameTransformer()
        self.transformer = transformer

    def fit(self, dataset: pd.DataFrame) -> "Transformer":
        self.transformer.fit(dataset)
        return self

    def transform(self, dataset: pd.DataFrame) -> pd.DataFrame:
        return self.transformer.transform(dataset)

    def fit_transform(self, dataset: pd.DataFrame) -> pd.DataFrame:
        return self.transformer.fit(dataset).transform(dataset)

    @defaults_from_attrs('transformer')
    def run(
        self, dataset: pd.DataFrame, transformer: BaseDataFrameTransformer = None
    ) -> Tuple[pd.DataFrame, Optional[BaseDataFrameTransformer]]:
        """
        Fit and apply a transformation on a dataset and return the fitted
        transformer and the new dataset.

        Parameters
        ----------
        dataset : pandas.DataFrame
            Dataset with data to be processed.

        Returns
        -------
        tuple of (pandas.DataFrame, BaseDataFrameTransformer)
            A tuple containing a pandas DataFrame with the transformed dataset
            and the fitted transformer.
        """
        self.dataset = dataset.copy()
        self.transformer = transformer  # type: ignore
        self.transformed_dataset = self.fit_transform(dataset)
        return self.transformed_dataset, self.transformer
