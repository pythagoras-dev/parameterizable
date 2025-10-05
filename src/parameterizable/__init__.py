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
    JsonSerializedParams: A dictionary-like object for accessing serialized parameters.

Functions:
    sort_dict_by_keys: Sort a dictionary by its keys alphabetically.
    dumps: Serialize an object's parameters into a JSON string.
    loads: Deserialize a JSON string back into an object.
    update_jsparams: Update parameters in a JSON-serialized string.
    access_jsparams: Access parameters in a JSON-serialized string.
"""

from .parameterizable import (
    # Classes
    ParameterizableClass
    )


from .dict_sorter import sort_dict_by_keys

from .json_processor import (
    JsonSerializedObject,
    loadjs,
    dumpjs,
    update_jsparams,
    access_jsparams)

__all__ = [
    'sort_dict_by_keys',
    'ParameterizableClass',
    "loadjs",
    "dumpjs",
    'JsonSerializedObject',
    'update_jsparams',
    'access_jsparams'
]
