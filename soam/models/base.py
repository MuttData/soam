from abc import abstractmethod

from sklearn.base import BaseEstimator, TransformerMixin


class BaseModel(BaseEstimator, TransformerMixin):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def fit_transform(self, X, y=None, **fit_params):
        pass

    @abstractmethod
    def fit(self, X, y=None, copy=True, **fit_params):
        pass

    @abstractmethod
    def predict(self, X, copy=True):
        pass

    @abstractmethod
    def get_params(self, deep=True):
        pass

    @abstractmethod
    def set_params(self, **params):
        pass

    @abstractmethod
    def __repr__(self):  # pylint:disable=signature-differs
        pass
