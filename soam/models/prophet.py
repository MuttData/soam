from collections import OrderedDict
from copy import deepcopy
from inspect import signature

from fbprophet import Prophet
import numpy as np
import pandas as pd

from soam.models.base import BaseModel


def as_np_vector(y):
    """Ensures a list, tuple, pandas.Series, pandas.DataFrame
    or numpy.ndarray is returned as a numpy.ndarray of dimension 1.

    Parameters
    ----------
    y: list, tuple, numpy.ndarray, pandas.Series, pandas.DataFrame
        The object containing the y values to fit.
        If y is multidimensional, e.g.: [[1, 2], [3, 4]], the first column
        will be returned as y value, continuining the example: [1, 3].

    Returns
    -------
    numpy.ndarray of dimension 1
        The values as a numpy array of dimension 1.
    """
    if isinstance(y, (list, tuple)):
        y = np.asarray(y)
    elif isinstance(y, (pd.Series, pd.DataFrame)):
        y = y.values
    if isinstance(y, np.ndarray):
        if len(y.shape) > 1:
            y = y[:, 0]
    return y


class SkProphet(BaseModel):
    DS = "ds"

    def __init__(
        self,
        date_column: str,
        yhat_only: bool = True,
        extra_regressors=OrderedDict({}),
        **prophet_kwargs,
    ):
        """Scikit learn compatible interface for FBProphet.

        Parameters
        ----------
        date_column: str
            Name of the column to use as date in Prophet.
        yhat_only= Boolean
            True to return only the yhat from Prophet predictions.
            False to return everything.
        extra_regressors: [] or [str] or [dict()]
            List with extra regressors to use. The list can have:
            * strings: column names (default prophet arguments for extra
              regressors will be used).
            * dicts: {name: *column_name*, prior_scale: _, standardize: _,
                      mode: _}
              For more information see Prophet.add_regressors.
        prophet_kwargs: dict
            Keyword arguments to forward to Prophet.
        """
        super().__init__()
        self.date_column = date_column
        self.yhat_only = yhat_only
        self.extra_regressors = extra_regressors
        self.prophet_kwargs = prophet_kwargs
        self._set_my_extra_regressors()
        self.model = None

    def fit(self, X, y=None, copy=True, **fit_params):
        """Scikit learn's like fit on the Prophet model.

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
            prophet with those names.
            If False is provided, the input data will be copied and the copy
            modified if required.
        fit_params: keyword arguments
            Keyword arguments to forward to Prophet's fit.
        """
        if not isinstance(X, pd.DataFrame):
            raise TypeError('Arg "X" passed can only be of pandas.DataFrame type.')
        if copy:
            X = X.copy()
        if self.date_column != self.DS and self.date_column in X.columns:
            X = X.rename({self.date_column: self.DS}, axis=1)
        if y is not None:
            if isinstance(y, str) and y in X.columns:
                X = X.rename({y: 'y'}, axis=1)
            else:
                X['y'] = as_np_vector(y)
        self.model = Prophet(**self.prophet_kwargs)
        return self.model.fit(X, **fit_params)

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
            prophet with those names.
            If False is provided, the input data will be copied and the copy
            modified if required.
        """
        if self.date_column != self.DS and self.date_column in X.columns:
            X = X.rename({self.date_column: self.DS}, axis=1)
        predictions = self.model.predict(X)
        if self.yhat_only:
            predictions = predictions.yhat.values

        return predictions.rename({self.DS: self.date_column}, axis=1)

    def transform(self, X):
        """Scikit learn's transform"""
        return self.predict(X)

    def fit_transform(self, X, y=None, **fit_params):
        """Scikit learn's fit_transform"""
        self.fit(X, y, **fit_params)
        return self.transform(X)

    def get_params(self, deep=True):
        """Scikit learn's get_params (returns the estimator's params)."""
        prophet_attrs = [
            attr for attr in signature(Prophet.__init__).parameters if attr != 'self'
        ]
        sk_attrs = [
            attr for attr in signature(self.__init__).parameters if attr != 'self'
        ]
        prophet_params = {a: getattr(self, a, None) for a in prophet_attrs}
        sk_params = {a: getattr(self, a, None) for a in sk_attrs}
        if deep:
            sk_params = deepcopy(sk_params)
            prophet_params = deepcopy(prophet_params)
        sk_params['prophet_kwargs'].update(prophet_params)
        return sk_params

    def set_params(self, **params):
        """Scikit learn's set_params (sets the parameters provided).
        Note on prophet keyword arguments precedence; this applies:
           _First, if some argument is explicitly provided, this value will be
            kept.
           _If not, but provided inside a 'prophet_kwargs' dict, the last is
            kept.
           _Lastly, if not provided in neither way but currently set, the value
            is not erased.
        """
        sk_kws = [
            attr for attr in signature(self.__init__).parameters if attr != 'self'
        ]
        current_prophet_kws = getattr(self, 'prophet_kwargs', {})
        explicit_prophet_kws = {}
        args_passed_prophet_kws = {}
        for attr, value in params.items():
            if attr == 'prophet_kwargs':
                explicit_prophet_kws = value
            elif attr not in sk_kws:
                args_passed_prophet_kws[attr] = value
            else:
                setattr(self, attr, value)
        prophet_kws = current_prophet_kws
        prophet_kws.update(explicit_prophet_kws)
        prophet_kws.update(args_passed_prophet_kws)
        for attr, value in prophet_kws.items():
            setattr(self, attr, value)
        setattr(self, 'prophet_kwargs', prophet_kws)
        self._set_my_extra_regressors()
        return self

    def _set_my_extra_regressors(self):
        """Adds the regressors defined in self.extra_regressors.
        It is meant to be used at initialization.
        """
        if self.extra_regressors:
            self.extra_regressors = self.extra_regressors.__class__()
            for regressor in self.extra_regressors:
                if isinstance(regressor, str):
                    self.model.add_regressor(regressor)
                elif isinstance(regressor, dict):
                    self.model.add_regressor(**regressor)
                else:
                    raise TypeError(
                        'Invalid extra_regressor in SkProphet.'
                        'Extra regressors must be strings or dicts with '
                        '{name: *column_name*, prior_scale: _, standardize: _, '
                        'mode: _}'
                    )

    def __repr__(self):
        """Text representation of the object to look it nicely in the
        interpreter.
        """
        return (
            f'{self.__class__.__name__}('
            f'date_column="{self.date_column}", '
            f'yhat_only={self.yhat_only}, '
            f'extra_regressors={self.extra_regressors}'
            f'prophet_kwargs={self.prophet_kwargs})'
        )

    __str__ = __repr__
