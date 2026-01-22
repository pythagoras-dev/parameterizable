"""Basic infrastructure for parameterizable classes.

This module provides functionality for working with parameterizable classes:
classes that have (hyper)parameters which define an object's
configuration/identity, but not its internal contents or data.
Such parameters are typically passed to the __init__ method.

The module provides an API for getting parameter values from an object,
and for converting the parameters to and from a portable dictionary
(a dictionary with sorted str keys that only contains
basic types and portable sub-dictionaries).
"""
import inspect
from typing import Any

from ..utility_functions.dict_sorter import sort_dict_by_keys
from ..utility_functions.json_processor import dumpjs, JsonSerializedObject


class ParameterizableMixin:
    """Base class for parameterizable classes.

    Classes deriving from this base expose a stable set of configuration
    parameters that define their behavior and identity. Subclasses implement
    get_params to return these parameters, which can then be serialized to
    and from a portable JSON representation.

    Note:
        This class is intended to be subclassed. The default implementation of
        get_params returns an empty mapping.
    """

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.get_params()})"

    def get_params(self) -> dict[str, Any]:
        """Return this instance's configuration parameters.

        Parameters define the object's configuration but not its internal
        contents or data. They are typically passed to __init__ at creation time.

        Returns:
            A mapping of parameter names to values.

        Note:
            Subclasses should override this method to return their specific
            parameters. The default implementation returns an empty dictionary.
        """
        params = dict()
        return params


    def get_jsparams(self) -> JsonSerializedObject:
        """Return this instance's parameters encoded as JSON.

        Returns:
            JSON string produced by dumpjs.
        """
        return dumpjs(sort_dict_by_keys(self.get_params()))


    @classmethod
    def get_default_params(cls) -> dict[str, Any]:
        """Get the default parameters of the class as a dictionary.

        Default values are taken from keyword parameters of __init__ and
        returned as a key-sorted dictionary. Subclasses may override if default
        computation requires custom logic.

        Returns:
            The class's default parameters sorted by key.
        """
        signature = inspect.signature(cls.__init__)
        # Skip the first parameter (self/cls)
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
            JSON string with default parameters.
        """
        return dumpjs(cls.get_default_params())


    @property
    def essential_param_names(self) -> set[str]:
        """Names of parameters that define the object's core identity and behavior.
        
        Essential parameters are those that fundamentally define an object's behavior
        or identity - for example, the maximum number of trees in a random forest
        or the maximum depth of a decision tree.
        
        These parameters are oftentimes immutable throughout the object's lifetime.
        They are guaranteed to be preserved during the copying/deepcopying,
        serialization/deserialization processes, and similar operations.
        
        Note:
            Subclasses should override this property to specify which parameters are
            essential. The default implementation considers all parameters essential.
        
        Returns:
            Names of essential parameters.
        """
        return set(self.get_params().keys())


    @property
    def auxiliary_param_names(self) -> set[str]:
        """Names of the object's auxiliary parameters.

        Auxiliary parameters are parameters that do not fundamentally impact
        the object's behavior or identity. These parameters
        might include settings like logging verbosity, debug flags,
        or probability thresholds for consistency checks.

        They are considered "disregardable" in the sense that they are not
        guaranteed to be preserved during serialization/deserialization
        processes, or even during simple copying/deepcopying operations.

        Returns:
            Set of auxiliary parameter names.
        """
        return set(self.get_params().keys()) - self.essential_param_names


    def get_essential_params(self) -> dict[str, Any]:
        """Return only the essential parameters.

        Returns:
            Mapping of essential parameter names to values.
        """
        return {k: v for k, v in self.get_params().items()
                if k in self.essential_param_names}


    def get_essential_jsparams(self) -> JsonSerializedObject:
        """Return essential parameters encoded as JSON.

        Returns:
            JSON string with essential parameters.
        """
        return dumpjs(self.get_essential_params())


    def get_auxiliary_params(self) -> dict[str, Any]:
        """Return only the auxiliary parameters.

        Returns:
            Mapping of auxiliary parameter names to values.
        """
        return {k: v for k, v in self.get_params().items()
                if k in self.auxiliary_param_names}


    def get_auxiliary_jsparams(self) -> JsonSerializedObject:
        """Return auxiliary parameters encoded as JSON.

        Returns:
            JSON string with auxiliary parameters.
        """
        return dumpjs(self.get_auxiliary_params())
