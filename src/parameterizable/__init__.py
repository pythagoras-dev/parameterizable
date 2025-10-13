"""Tools for working with parameterizable classes.

This package provides infrastructure for classes whose behavior is configured
by (hyper)parameters, typically passed to their ``__init__`` method. It offers
helpers to retrieve parameters from objects and to convert parameters to and
from a portable, JSON-serializable dictionary.

Public API:
- ParameterizableClass: Base class for parameterizable objects.
- NotPicklableClass: Mixin that prevents pickling/unpickling.
- sort_dict_by_keys: Sort a dictionary by its keys alphabetically.
- dumpjs: Serialize an object (or parameters) into a JSON string.
- loadjs: Deserialize a JSON string produced by ``dumpjs`` back into a Python object.
- update_jsparams: Update parameters in a JSON-serialized string.
- access_jsparams: Access parameters in a JSON-serialized string.
- JsonSerializedObject: NewType alias for JSON strings produced by ``dumpjs``.
"""

from importlib import metadata as _md
__version__ = _md.version("parameterizable")

from .dict_sorter import sort_dict_by_keys

from .not_picklable import NotPicklableClass

from .json_processor import (
    JsonSerializedObject,
    loadjs,
    dumpjs,
    update_jsparams,
    access_jsparams
)

from .parameterizable import ParameterizableClass

__all__ = [
    'sort_dict_by_keys',
    'ParameterizableClass',
    'NotPicklableClass',
    'loadjs',
    'dumpjs',
    'JsonSerializedObject',
    'update_jsparams',
    'access_jsparams',
    '__version__'
]
