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
    """
    Provide an interface to transform pandas DataFrames.
    """

    def fit(
        self, X: pd.DataFrame, **fit_params  # pylint:disable=unused-argument
    ) -> "BaseDataFrameTransformer":
        """
        Fit method

        Parameters
        ----------
        X: pandas.DataFrame
            DataFrame to fit.
        """
        logger.warning("Subclasses should implement this.")
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform method.

        Parameters
        ----------
            X: pd.DataFrame
                DataFrame to be transformed.

        Raises
        ------
            NotImplementedError
                Raises error if its not a subclass.

        Returns
        -------
            pd.DataFrame
        """
        raise NotImplementedError("Subclasses should implement this.")

    def fit_transform(self, X: pd.DataFrame, **fit_params) -> pd.DataFrame:
        """
        Fit Transform method.

        Parameters
        ----------
            X: pd.DataFrame
                DataFrame to be fitted and transformed.

        Returns
        -------
            pd.DataFrame
                DataFrame fitted and transformed.
        """
        return self.fit(X, **fit_params).transform(X)


class DummyDataFrameTransformer(BaseDataFrameTransformer):
    """
    This transformer provides an "identity transformation.
    Returns its input without any alteration.
    """

    def __init__(self):
        pass

    def fit(self, df_X):  # pylint:disable=unused-argument
        """
        Fit method

        Parameters
        ----------
            df_X: pandas.DataFrame
                DataFrame to be fitted.
        """
        return self

    def transform(self, df_X, inplace=True):
        """
        Transform method

        Parameters
        ----------
            df_X: pandas.DataFrame
                DataFrame to be transformed.
            inplace: bool
                Whether the changes should persist in the DataFrame or not. Default is True.

        Returns
        -------
            pandas.DataFrame
                DataFrame transformed.
        """
        if not inplace:
            df_X = df_X.copy()
        return df_X


class Transformer(Step):
    """
    Generates the transformer object.
    """

    transformer: BaseDataFrameTransformer

    def __init__(
        self,
        transformer: BaseDataFrameTransformer = None,
        savers: "Optional[List[Saver]]" = None,
        **kwargs
    ):
        """
        Handle transformations

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
        """
        Fit method

        Parameters
        ----------
            dataset: pandas.DataFrame
                DataFrame to be fitted.
        """
        self.transformer.fit(dataset)
        return self

    def transform(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """
        Transform method

        Parameters
        ----------
            dataset: pandas.DataFrame
                DataFrame to be transformed.

        Returns
        -------
            pd.DataFrame
                DataFrame transformed.
        """
        return self.transformer.transform(dataset)

    def fit_transform(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """Fit Transform method.

        Parameters
        ----------
            dataset: pd.DataFrame
                DataFrame to be fitted and transformed.

        Returns
        -------
            pd.DataFrame
                DataFrame fitted and transformed.
        """
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
