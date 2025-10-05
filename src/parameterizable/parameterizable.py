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