from copy import deepcopy
from inspect import isclass
import logging

from sklearn.base import BaseEstimator

logger = logging.getLogger(__name__)


class Classer:
    def __init__(self, EstimatorClass):
        """Wraps an EstimatorClass to avoid sklearn.base.clone exploting when
        called against an EstimatorClass during grid search of metaestimators.

        Parameters
        ----------
        EstimatorClass: class
            A sklearn compatible estimator class.
        """
        self._class = EstimatorClass

    def new(self, *args, **kwargs):
        """Returns a new instance of the wrapped class initialized with the
        args and kwargs.
        """
        return self._class(*args, **kwargs)

    @classmethod
    def from_obj(cls, obj):
        """Initializes a new classer from an object, which can be another
        Classer, a class or an instance.
        """
        if isinstance(obj, Classer):
            return obj
        elif isclass(obj):
            return Classer(obj)
        else:
            return Classer(obj.__class__)

    def __eq__(self, other):
        """Equality checks inner class wrapped."""
        return self.__class__ == other.__class__ and self._class == other._class

    def __repr__(self):
        """Text representation of the object to look it nicely in the
        interpreter.
        """
        return '%s(%s)' % (self.__class__.__name__, self._class.__name__)

    __str__ = __repr__


class DaysSelectorEstimator(BaseEstimator):
    def __init__(
        self, estimator_class, amount_of_days, estimator_kwargs=None, sort_col='date'
    ):
        """An estimator that only uses a certain amount of rows on fit.

        Parameters
        ----------
        estimator_class: Classer or Estimator Class or estimator instance
            Estimator class to use to fit, if an Estimator Class is provided
            it will be wrapped with a metaestimator.Classer, if a instance
            is provided, its classed will be wrapped.
            examples:
            - Classer(sklearn.ensemble.RandomForestRegressor)
            - sklearn.ensemble.RandomForestRegressor
            - sklearn.ensemble.RandomForestRegressor()
        amount_of_days: int
            The amount of days to use for training.
        sort_col: str
            Name of the column which will be used for sorting if X is a
            dataframe and has the column.
        estimator_kwargs: dict
            Keyword arguments to initialize EstimatorClass

        E.g.:

        > DaysSelectorEstimator(RandomForestRegressor(), 100)
        """
        self.amount_of_days = amount_of_days
        self.sort_col = sort_col
        self.estimator_kwargs = estimator_kwargs
        self.estimator_class = Classer.from_obj(estimator_class)
        self._estimator = self.estimator_class.new(**self.estimator_kwargs)
        self._is_fit = False
        self._fit_cols = None

    @property
    def feature_names_(self):
        if self._fit_cols is not None:
            return self._fit_cols
        if not self._is_fit:
            raise ValueError("Estimator not fit: feature names not available")
        raise ValueError("Feature names not available")

    @property
    def feature_importances_(self):
        return self._estimator.feature_importances_

    def fit(self, X, y):
        """Fits self.estimator only to the last self.amount_of_days rows.
        Tries to sort X first.

        Parameters
        ----------
        X: pd.DataFrame
            A dataframe to fit.
        y: vector like
            Labels
        """
        if self.sort_col in X.columns:
            X = X.sort_values(self.sort_col, axis=0)
        index_to_drop = X.iloc[: -self.amount_of_days].index
        y = y.drop(index_to_drop).reset_index(drop=True)
        X = X.drop(index_to_drop).reset_index(drop=True)
        self._estimator.fit(X, y)
        try:
            self._fit_cols = X.columns
        except AttributeError:
            pass
        self._is_fit = True
        return self

    def predict(self, X):
        """Scikit's learn like predict."""
        return self._estimator.predict(X)

    def get_params(self, deep=True):
        """Get estimator params."""
        kwargs = self.estimator_kwargs
        if deep:
            kwargs = deepcopy(kwargs)
        return {
            'estimator_class': self.estimator_class,
            'amount_of_days': self.amount_of_days,
            'sort_col': self.sort_col,
            'estimator_kwargs': kwargs,
        }

    def set_params(self, **params):
        """Sets the estimator's params to **params."""
        self.estimator_class = Classer.from_obj(params['estimator_class'])
        self.amount_of_days = params['amount_of_days']
        self.sort_col = params['sort_col']
        self.estimator_kwargs = params['estimator_kwargs']
        self._estimator = self.estimator_class.new(**self.estimator_kwargs)
        return self
