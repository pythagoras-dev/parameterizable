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

    This class provides the basic functionality for parameterizable classes:
    classes that have (hyper) parameters which define an object's configuration
    and which are typically passed to the .__init__() method.
    The class provides an API for getting parameters' values from an object
    and for converting the parameters to and from a portable dictionary
    (a dictionary that only contains basic types
    and portable sub-dictionaries).

    Note:
        This class is not meant to be used directly but to be subclassed
        by classes that need to be parameterizable.
    """


    def get_params(self) -> dict[str, Any]:
        """Get the parameters of the object as a dictionary.

        This method must be implemented by subclasses.

        These parameters define the object's configuration,
        but not its internal contents or data. They are typically passed
        to the .__init__() method of the object at the time of its creation.

        Returns:
            dict[str, Any]: A dictionary containing the object's parameters
                with string keys and arbitrary values.
        """
        params = dict()
        return params


    def get_jsparams(self) -> JsonSerializedObject:
        """Get the parameters of the object as a JSON string."""
        return dumpjs(self.get_params())


    @classmethod
    def get_default_params(cls) -> dict[str, Any]:
        """Get the default parameters of the class as a dictionary.

        Default parameters are the values that are used to
        configure an object if no arguments are explicitly passed to
        the .__init__() method.

        This implementation inspects the __init__() method of the class to get
        the default parameters. Subclasses can override this method to provide
        default parameters if the logic for determining defaults is more
        complex than what can be inferred from the __init__ signature.

        Returns:
            dict[str, Any]: A dictionary containing the class's default parameters
                with string keys and arbitrary values, sorted by key.
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
        """Get the default parameters of the class as a JSON string."""
        return dumpjs(cls.get_default_params())


    @property
    def essential_param_names(self) -> set[str]:
        """Get the names of the object's essential parameters.

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
        """Get the essential parameters of the object."""
        return {k:v for k,v in self.get_params().items()
                if k in self.essential_param_names}


    def get_essential_jsparams(self) -> JsonSerializedObject:
        """Get the essential parameters of the object as a JSON string."""
        return dumpjs(self.get_essential_params())


    def get_auxiliary_params(self) -> dict[str,Any]:
        """Get the auxiliary parameters of the object."""
        return {k:v for k,v in self.get_params().items()
            if k in self.auxiliary_param_names}


    def get_auxiliary_jsparams(self) -> JsonSerializedObject:
        """Get the auxiliary parameters of the object as a JSON string."""
        return dumpjs(self.get_auxiliary_params())
