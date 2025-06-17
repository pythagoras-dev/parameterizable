"""Package for working with parameterizable classes.

This package provides functionality for working with parameterizable classes:
classes that have (hyper) parameters which define an object's configuration,
but not its internal contents or data. Such parameters are typically
passed to the .__init__() method.

The package provides an API for getting parameters' values from an object,
and for converting the parameters to and from a portable dictionary
(a dictionary with sorted str keys that contains values with
only basic types and portable sub-dictionaries).
"""

from .parameterizable import (
    # Classes
    ParameterizableClass,

    # Functions
    get_object_from_portable_params,
    is_parameterizable,
    _register_parameterizable_class,
    is_registered,

    # Constants
    CLASSNAME_PARAM_KEY
)

__all__ = [
    'ParameterizableClass',
    'get_object_from_portable_params',
    'is_parameterizable',
    'is_registered',
    'CLASSNAME_PARAM_KEY'
]
