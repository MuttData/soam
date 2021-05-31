"""Wrapping functions for SkLearn API."""
import abc
from abc import abstractmethod
import inspect
from types import FunctionType
from typing import Callable, List

from sklearn.base import BaseEstimator


def get_clean_parameter_dict(signature: inspect.Signature) -> dict:
    """Remove self, kwarg and positional params from signature.

    Parameters
    ----------
    signature : inspect.Signature
        signature of a method

    Returns
    -------
    dict
        clean parameter dictionary
    """
    return {
        p.name: p.default if p.default != inspect.Parameter.empty else None
        for p in signature.parameters.values()
        if p.name != "self" and p.kind != p.VAR_KEYWORD and p.kind != p.VAR_POSITIONAL
    }


def sk_constructor_wrapper(modeltype) -> Callable:
    """Constructor patching decorator."""

    def sk_construct_function(init_func: Callable):
        """
        Join sklearn's and model's constructors.
        Ref: https://github.com/heidelbergcement/hcrystalball/blob/master/src/hcrystalball/wrappers/_base.py
        """
        orig_signature = inspect.signature(init_func)
        orig_parameters = get_clean_parameter_dict(orig_signature)

        model_signature = inspect.signature(modeltype.__init__)
        model_parameters = get_clean_parameter_dict(model_signature)

        full_parameter_names = list(model_parameters) + list(orig_parameters)
        full_parameter_defaults = list(model_parameters.values()) + list(
            orig_parameters.values()
        )
        assignments = "; ".join([f"self.{p}={p}" for p in full_parameter_names])

        constructor_code = compile(
            f'def __init__(self, {", ".join(full_parameter_names)}): ' f"{assignments}",
            "<string>",
            "exec",
        )

        modified_init_function = FunctionType(
            constructor_code.co_consts[0],  # code
            globals(),  # global dict
            "__init__",  # name of function
            tuple(full_parameter_defaults),  # defaults
        )

        return modified_init_function

    return sk_construct_function


class SkWrapper(BaseEstimator, metaclass=abc.ABCMeta):
    """Base class for model wrappers."""

    @abstractmethod
    def __init__(self):
        pass

    def _init_sk_model(
        self, model_class, clean=False, ignore_params: List[str] = None, **kwargs
    ) -> BaseEstimator:
        """Instantiate model_class.

        Parameters
        ----------
        model_class :
            Class of the model to wrap.
        clean : bool, optional
            Whether to check if param corresponds to
            the model's constructor or not, by default False
        ignore_params : List[str], optional
            Extra parameters specified in wrapper to be ignored, by default None
            i.e wrapper parameters that don't belong to the model.

        Returns
        -------
        Object's instance.
        """
        model_signature = inspect.signature(model_class.__init__)
        ignore_params = ignore_params or []
        model_params = orig_params = self.get_params()
        if clean:
            model_params = get_clean_parameter_dict(model_signature)
        params = {
            k: orig_params[k] for k, v in model_params.items() if k not in ignore_params
        }

        return model_class(**{**params, **kwargs})
