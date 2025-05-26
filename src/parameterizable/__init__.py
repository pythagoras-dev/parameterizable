"""Package for working with parameterizable classes.

This package provides functionality for working with parameterizable classes:
classes that have (hyper) parameters which define object's configuration,
but not its internal contents or data. Such parameters are typically
passed to the .__init__() method.

The package provides an API for getting parameters' values from an object,
and for converting the parameters to and from a portable dictionary
(a dictionary that only contains basic types and portable sub-dictionaries).
"""

from src.parameterizable.parameterizable import (
    # Classes
    ParameterizableClass,

    # Functions
    get_object_from_portable_params,
    is_parameterizable,
    register_parameterizable_class,
    is_registered
)

__all__ = [
    'ParameterizableClass',
    'get_object_from_portable_params',
    'is_parameterizable',
    'register_parameterizable_class',
    'is_registered'
]
