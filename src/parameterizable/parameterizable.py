"""Package with basic infrastructure for parameterizable classes.

This package provides the functionality for work with parameterizable classes:
classes that have (hyper) parameters which define an object's configuration,
but not its internal contents or data. Such parameters are typically
passed to the .__init__() method.

The package provides an API for getting parameters' values from an object,
and for converting the parameters to and from a portable dictionary
(a dictionary with sorted str keys that only contains
basic types and portable sub-dictionaries).
"""
import inspect
from typing import Any

from .dict_sorter import sort_dict_by_keys
from .json_processor import loadjs,dumpjs, JsonSerializedObject


class ParameterizableClass:
    """Base class for parameterizable classes.

    Classes deriving from this base expose a stable set of configuration
    parameters that define their behavior. Subclasses implement ``get_params()``
    to return these parameters, which can then be serialized to and from
    a portable JSON representation.

    Note:
        This class is intended to be subclassed. The default implementation of
        ``get_params()`` returns an empty mapping.
    """


    def get_params(self) -> dict[str, Any]:
        """Return this instance's configuration parameters.

        This method must be implemented by subclasses.

        These parameters define the object's configuration,
        but not its internal contents or data. They are typically passed
        to the .__init__() method of the object at the time of its creation.

        Returns:
            dict[str, Any]: A mapping of parameter names to values.
        """
        params = dict()
        return params


    def get_jsparams(self) -> JsonSerializedObject:
        """Return this instance's parameters encoded as JSON.

        Returns:
            JsonSerializedObject: JSON string produced by ``dumpjs``.
        """
        return dumpjs(self.get_params())


    @classmethod
    def get_default_params(cls) -> dict[str, Any]:
        """Get the default parameters of the class as a dictionary.

        Default values are taken from keyword parameters of ``__init__`` and
        returned as a key-sorted dictionary. Subclasses may override if default
        computation requires custom logic.

        Returns:
            dict[str, Any]: The class's default parameters sorted by key.
        """
        signature = inspect.signature(cls.__init__)
        # The first parameter of __init__ is the instance itself (e.g. 'self')
        # We are skipping it.
        params_to_consider = list(signature.parameters.values())[1:]
        params = {
            p.name: p.default
            for p in params_to_consider
            if p.default is not inspect.Parameter.empty
        }
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


    @classmethod
    def get_default_jsparams(cls) -> JsonSerializedObject:
        """Return default constructor parameters encoded as JSON.

        Returns:
            JsonSerializedObject: JSON string with default parameters.
        """
        return dumpjs(cls.get_default_params())


    @property
    def essential_param_names(self) -> set[str]:
        """Names of parameters that define the object's identity/behavior.

        Essential parameters are the parameters that define the substance of
        the object's behavior and/or identity, e.g. the max number of
        decision trees in a forest or max depth of a tree.

        In most cases, the essential parameters are immutable (do not
        change during the lifetime of the object).
        """
        return set(self.get_default_params().keys())


    @property
    def auxiliary_param_names(self) -> set[str]:
        """Get the names of the object's auxiliary parameters.

        Auxiliary parameters are the parameters that do not impact the substance
        of the object's behavior and/or identity, e.g. logging verbosity
        or probability of random consistency checks.
        """
        return set(self.get_params().keys()) - self.essential_param_names


    def get_essential_params(self) -> dict[str, Any]:
        """Return only the essential parameters.

        Returns:
            dict[str, Any]: Mapping of essential parameter names to values.
        """
        return {k: v for k, v in self.get_params().items()
                if k in self.essential_param_names}


    def get_essential_jsparams(self) -> JsonSerializedObject:
        """Return essential parameters encoded as JSON.

        Returns:
            JsonSerializedObject: JSON string with essential parameters.
        """
        return dumpjs(self.get_essential_params())


    def get_auxiliary_params(self) -> dict[str, Any]:
        """Return only the auxiliary parameters.

        Returns:
            dict[str, Any]: Mapping of auxiliary parameter names to values.
        """
        return {k: v for k, v in self.get_params().items()
                if k in self.auxiliary_param_names}


    def get_auxiliary_jsparams(self) -> JsonSerializedObject:
        """Return auxiliary parameters encoded as JSON.

        Returns:
            JsonSerializedObject: JSON string with auxiliary parameters.
        """
        return dumpjs(self.get_auxiliary_params())
