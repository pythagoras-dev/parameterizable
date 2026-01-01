"""Tools for working with mixinforge classes.

This package provides reusable mixins and utility functions that help you build
well-structured Python classes. It offers tools for parameter management, cache
management, initialization control, thread safety, pickle prevention, JSON
serialization, and dictionary utilities.

Public API:
- ParameterizableMixin: Base class for parameterizable objects with JSON serialization.
- CacheablePropertiesMixin: Automatic discovery and invalidation of cached_property attributes.
- NotPicklableMixin: Mixin that prevents pickling/unpickling.
- SingleThreadEnforcerMixin: Enforces single-threaded execution with multi-process support.
- GuardedInitMeta: Metaclass for strict initialization control and lifecycle hooks.
- sort_dict_by_keys: Sort a dictionary by its keys alphabetically.
- dumpjs: Serialize an object (or parameters) into a JSON string.
- loadjs: Deserialize a JSON string produced by dumpjs back into a Python object.
- update_jsparams: Update parameters in a JSON-serialized string.
- access_jsparams: Access parameters in a JSON-serialized string.
- JsonSerializedObject: NewType alias for JSON strings produced by dumpjs.
"""

from importlib import metadata as _md
try:
    __version__ = _md.version("mixinforge")
except _md.PackageNotFoundError:
    __version__ = "unknown"

from .dict_sorter import sort_dict_by_keys

from .not_picklable_mixin import NotPicklableMixin

from .json_processor import (
    JsonSerializedObject,
    loadjs,
    dumpjs,
    update_jsparams,
    access_jsparams
)

from .parameterizable_mixin import ParameterizableMixin

from .cacheable_properties_mixin import CacheablePropertiesMixin

from .guarded_init_metaclass import GuardedInitMeta

from .single_thread_enforcer_mixin import SingleThreadEnforcerMixin

__all__ = [
    'CacheablePropertiesMixin',
    'GuardedInitMeta',
    'SingleThreadEnforcerMixin',
    'sort_dict_by_keys',
    'ParameterizableMixin',
    'NotPicklableMixin',
    'loadjs',
    'dumpjs',
    'JsonSerializedObject',
    'update_jsparams',
    'access_jsparams',
    '__version__'
]
