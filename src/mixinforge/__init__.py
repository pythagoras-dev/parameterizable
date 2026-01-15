"""Tools for working with mixinforge classes.

This package provides reusable mixins and utility functions that help you build
well-structured Python classes. It offers tools for parameter management, cache
management, initialization control, thread safety, pickle prevention, JSON
serialization, and dictionary utilities.

Public API:
- ParameterizableMixin: Base class for parameterizable objects with JSON serialization.
- ImmutableMixin: Base class for immutable objects with customizable identity keys.
- ImmutableParameterizableMixin: Immutable objects with params-based identity.
- CacheablePropertiesMixin: Automatic discovery and invalidation of cached_property attributes.
- NotPicklableMixin: Mixin that prevents pickling/unpickling.
- SingleThreadEnforcerMixin: Enforces single-threaded execution with multi-process support.
- GuardedInitMeta: Metaclass for strict initialization control and lifecycle hooks.
- SingletonMixin: Ensures each subclass maintains exactly one instance.
- sort_dict_by_keys: Sort a dictionary by its keys alphabetically.
- dumpjs: Serialize an object (or parameters) into a JSON string.
- loadjs: Deserialize a JSON string produced by dumpjs back into a Python object.
- update_jsparams: Update parameters in a JSON-serialized string.
- access_jsparams: Access parameters in a JSON-serialized string.
- JsonSerializedObject: NewType alias for JSON strings produced by dumpjs.
"""

from ._version_info import __version__

from .utility_functions.dict_sorter import *
from .utility_functions.json_processor import *
from .utility_functions.nested_collections_processor import *
from .mixins_and_metaclasses.not_picklable_mixin import *
from .mixins_and_metaclasses.guarded_init_metaclass import *
from .mixins_and_metaclasses.parameterizable_mixin import *
from .mixins_and_metaclasses.immutable_mixin import *
from .mixins_and_metaclasses.immutable_parameterizable_mixin import *
from .mixins_and_metaclasses.cacheable_properties_mixin import *
from .mixins_and_metaclasses.single_thread_enforcer_mixin import *
from .mixins_and_metaclasses.singleton_mixin import *

__all__ = [
    'CacheablePropertiesMixin',
    'GuardedInitMeta',
    'ImmutableMixin',
    'ImmutableParameterizableMixin',
    'JsonSerializedObject',
    'NotPicklableMixin',
    'ParameterizableMixin',
    'SingleThreadEnforcerMixin',
    'SingletonMixin',
    '__version__',
    'access_jsparams',
    'dumpjs',
    'loadjs',
    'sort_dict_by_keys',
    'update_jsparams',
    'find_atomics_in_nested_collections',
    'find_nonatomics_inside_composite_object'
]
