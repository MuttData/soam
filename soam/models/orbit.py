"""
Orbit Interface Class
----------
Interface for Uber's Orbit to use in the forecast class.
"""
from copy import deepcopy
from inspect import signature
from typing import List

from orbit.models.dlt import DLTFull
from orbit.models.lgt import LGTFull
import pandas as pd

from soam.models.base import BaseModel

DLT_FULL = "dlt_full"
LGT_FULL = "lgt_full"
OBITS_MODELS = [DLT_FULL, LGT_FULL]


class SkOrbit(BaseModel):
    def __init__(
        self,
        date_column: str,
        yhat_only: bool = True,
        extra_regressors: List = [],
        orbit_model: str = DLT_FULL,
        **orbit_kwargs,
    ):
        """
        Forecast time series data with Orbit model.

        Parameters
        ----------
        date_column: str
            Name of the column to use as date in Orbit.
        yhat_only= Boolean
            True to return only the prediction from Orbit predictions.
            False to return everything.
        extra_regressors: []
            List with extra regressors to use column's names
        orbit_kwargs: dict
            Keyword arguments to forward to Orbit.
        """
        super().__init__()
        self.date_column = date_column
        self.yhat_only = yhat_only
        self.extra_regressors = extra_regressors
        self.orbit_kwargs = orbit_kwargs
        self.model = None
        self.orbit_model = orbit_model

    def fit(self, X, y=None, copy=True):
        """Scikit learn's like fit on the Orbit model.

        Parameters
        ----------
        X: pd.DataFrame
            A dataframe with the data to fit.
            It is expected to have a column with datetime values named as
            *self.date_column*.
        y: None or str or (list, tuple, numpy.ndarray, pandas.Series/DataFrame)
            The label values to fit. If y is:
            * None: the column 'y' should be contained in X.
            * str: the name of the column to use in X.
            * list, tuple, ndarray, etc: the values to fit.
              If the values have two dimensions (a matrix instead of a vector)
              the first column will be used.
              E.g.: [1, 3] -> [1, 3] will be used.
              E.g.: [[1], [3]] -> [1, 3] will be used.
              E.g.: [[1, 2], [3, 4]] -> [1, 3] will be used.
        copy: Boolean
            True to copy the input dataframe before working with it to avoid
            modifying the original one.
            If True is set, X should contain the `ds` and `y` columns for
            Orbit with those names.
            If False is provided, the input data will be copied and the copy
            modified if required.
        """
        if not isinstance(X, pd.DataFrame):
            raise TypeError('Arg "X" passed can only be of pandas.DataFrame type.')
        if copy:
            X = X.copy()
        if self.date_column not in X.columns:
            raise TypeError('Arg `date_col` passed not in columns.')
        if y is not None:
            if y not in X.columns:
                raise TypeError('Arg `response_col` passed not in columns.')
        orbit_args = {
            "response_col": y,
            "date_col": self.date_column,
        }
        orbit_args.update(self.orbit_kwargs)
        if self.orbit_model == DLT_FULL:
            self.model = DLTFull(**orbit_args)  # pylint: disable=too-many-function-args
        elif self.orbit_model == LGT_FULL:
            self.model = LGTFull(**orbit_args)  # pylint: disable=too-many-function-args
        else:
            raise TypeError(f'Unknown model type {self.orbit_model}.')
        return self.model.fit(X)

    def predict(self, X):
        """Scikit learn's predict (returns predicted values).

        Parameters
        ----------
        X: pandas.DataFrame
            Input data for predictions.
        copy: Boolean
            True to copy the input dataframe before working with it to avoid
            modifying the original one.
            If True is set, X should contain the `ds` and `y` columns for
            Orbit with those names.
            If False is provided, the input data will be copied and the copy
            modified if required.
        """
        predictions = self.model.predict(X)
        if self.yhat_only:
            predictions = predictions.prediction.values

        return predictions

    def transform(self, X):
        """Scikit learn's transform"""
        return self.predict(X)

    def fit_transform(self, X, y=None, **fit_params):
        """Scikit learn's fit_transform"""
        self.fit(X, y, **fit_params)
        return self.transform(X)

    def get_params(self, deep=True):
        """Scikit learn's get_params (returns the estimator's params)."""
        orbit_attrs = [
            attr for attr in signature(DLTFull.__init__).parameters if attr != 'self'
        ]
        sk_attrs = [
            attr for attr in signature(self.__init__).parameters if attr != 'self'
        ]
        orbit_params = {a: getattr(self, a, None) for a in orbit_attrs}
        sk_params = {a: getattr(self, a, None) for a in sk_attrs}
        if deep:
            sk_params = deepcopy(sk_params)
            orbit_params = deepcopy(orbit_params)
        sk_params['orbit_kwargs'].update(orbit_params)
        return sk_params

    def set_params(self, **params):
        """Scikit learn's set_params (sets the parameters provided).
        Note on Orbit keyword arguments precedence; this applies:
           _First, if some argument is explicitly provided, this value will be
            kept.
           _If not, but provided inside a 'Orbit_kwargs' dict, the last is
            kept.
           _Lastly, if not provided in neither way but currently set, the value
            is not erased.
        """
        sk_kws = [
            attr for attr in signature(self.__init__).parameters if attr != 'self'
        ]
        current_orbit_kws = getattr(self, 'Orbit_kwargs', {})
        explicit_orbit_kws = {}
        args_passed_orbit_kws = {}
        for attr, value in params.items():
            if attr == 'orbit_kwargs':
                explicit_orbit_kws = value
            elif attr not in sk_kws:
                args_passed_orbit_kws[attr] = value
            else:
                setattr(self, attr, value)
        orbit_kws = current_orbit_kws
        orbit_kws.update(explicit_orbit_kws)
        orbit_kws.update(args_passed_orbit_kws)
        for attr, value in orbit_kws.items():
            setattr(self, attr, value)
        setattr(self, 'Orbit_kwargs', orbit_kws)
        return self

    def __repr__(self):
        """Text representation of the object to look it nicely in the
        interpreter.
        """
        return (
            f'{self.__class__.__name__}('
            f'date_column="{self.date_column}", '
            f'yhat_only={self.yhat_only}, '
            f'extra_regressors={self.extra_regressors}'
            f'Orbit_kwargs={self.orbit_kwargs})'
        )

    __str__ = __repr__
