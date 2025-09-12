"""Package for working with parameterizable classes.

This package provides functionality for working with parameterizable classes:
classes that have (hyper) parameters which define an object's configuration,
but not its internal contents or data. Such parameters are typically
passed to the .__init__() method.

The package provides an API for getting parameters' values from an object,
and for converting the parameters to and from a portable dictionary
(a dictionary with sorted str keys that contains values with
only basic types and portable sub-dictionaries).

Classes:
    ParameterizableClass: Base class for parameterizable objects.

Functions:
    get_object_from_portable_params: Create objects from portable parameter dictionaries.
    is_parameterizable: Check if a class implements the parameterizable interface.
    register_parameterizable_class: Register a class for use with portable parameters.
    is_registered: Check if a class is registered in the parameterizable registry.
    smoketest_parameterizable_class: Run validation tests on a parameterizable class.
    sort_dict_by_keys: Sort a dictionary by its keys alphabetically.

Constants:
    CLASSNAME_PARAM_KEY: Key used to store class name in portable dictionaries.
"""

from .parameterizable import (
    # Classes
    ParameterizableClass,

    # Functions
    get_object_from_portable_params,
    is_parameterizable,
    register_parameterizable_class,
    is_registered,
    smoketest_parameterizable_class,

    # Constants
    CLASSNAME_PARAM_KEY
)

from .dict_sorter import sort_dict_by_keys

__all__ = [
    'ParameterizableClass',
    'get_object_from_portable_params',
    'is_parameterizable',
    'is_registered',
    'register_parameterizable_class',
    'smoketest_parameterizable_class',
    'CLASSNAME_PARAM_KEY',
    'sort_dict_by_keys'
]
