"""Utilities for detecting atomic types (leaf nodes) in object trees.

This module provides mechanisms to register and detect types that should
be treated as atomic (indivisible) during traversal or flattening operations,
supporting lazy loading to avoid unnecessary imports.
"""
from __future__ import annotations

import datetime
import decimal
import enum
import fractions
import pathlib
import re
import sys
import uuid
from functools import cache
from typing import Final, Iterable, TypeAlias, Union
import importlib

TypeSpec: TypeAlias = Union[type, "_LazyTypeDescriptor", tuple[str, str]]

class _TypeCouldNotBeImported:
    """Sentinel type for types that cannot be imported."""
    pass

class _LazyTypeDescriptor:
    """Defers type resolution until needed, avoiding expensive imports.

    Stores type information as strings (module and type names) or as an
    actual type object. The type is resolved lazily on first access via
    the type property.

    Attributes:
        module_name: Module name containing the type.
        type_name: Name of the type within its module.
        type: The resolved type object.
    """
    _eager_loading_mode: bool = False
    _module_name: str
    _type_name: str
    _actual_type: type | None

    def __init__(self, type_spec: TypeSpec):
        """Initialize the descriptor with type information.

        Args:
            type_spec: Type specification. Can be a LazyTypeDescriptor
                (copies state), a type object, or a tuple of (module_name,
                type_name) strings.

        Raises:
            ValueError: If the tuple does not have exactly 2 elements or
                contains empty strings.
            TypeError: If type_spec is not a supported type.
        """
        if isinstance(type_spec, _LazyTypeDescriptor):
            self._module_name = type_spec._module_name
            self._type_name = type_spec._type_name
            self._actual_type = type_spec._actual_type
        elif isinstance(type_spec, type):
            self._actual_type = type_spec
            self._module_name = type_spec.__module__
            self._type_name = type_spec.__qualname__
        elif isinstance(type_spec, tuple):
            if len(type_spec) != 2:
                raise ValueError(f"Tuple must have exactly 2 elements (module_name, type_name), got {len(type_spec)}")
            module_name, type_name = type_spec
            if not isinstance(module_name, str) or not module_name:
                raise ValueError(f"'module_name' must be a non-empty string, got {module_name!r}")
            if not isinstance(type_name, str) or not type_name:
                raise ValueError(f"'type_name' must be a non-empty string, got {type_name!r}")
            self._module_name = module_name
            self._type_name = type_name
            self._actual_type = None
        else:
            raise TypeError(
                f"'type_spec' must be a LazyTypeDescriptor, type, or tuple[str, str], "
                f"got {type(type_spec).__name__}: {type_spec!r}"
            )

        if self._eager_loading_mode:
            _ = self.type

    @property
    def eager_loading_mode(self) -> bool:
        """Whether to load/import types eagerly.

        This mode mostly exists for testing purposes.
        """
        return self._eager_loading_mode

    @property
    def module_name(self) -> str:
        """Module name containing the type."""
        return self._module_name

    @property
    def type_name(self) -> str:
        """Type name within its module."""
        return self._type_name

    @property
    def type(self) -> type:
        """The resolved type object.

        Import occurs on first access. Returns a sentinel type if the import
        fails.
        """
        if self._actual_type is not None:
            return self._actual_type

        try:
            module = importlib.import_module(self.module_name)
            # Handle nested classes (e.g., 'Outer.Inner')
            current_object = module
            for part in self.type_name.split('.'):
                current_object = getattr(current_object, part)
            self._actual_type = current_object
        except Exception:
            self._actual_type = _TypeCouldNotBeImported
            # Sentinel value indicating a type could not be imported.
            # Later comparison checks against this value will always fail.
            # It is intentionally stored the first time the type is accessed
            # and is never retried. We do not support scenarios where a
            # new package is installed after the first access attempt.

        return self._actual_type


class _LazyTypeRegistry:
    """Registry for types that should be treated as atomic.

    Maintains a collection of type descriptors to check if an object's type
    is registered as atomic. Supports lazy resolution to avoid premature
    imports.

    Uses a dual-key index (module name and type name) to robustly handle
    type aliases and re-exports.
    """

    _indexed_types: dict[str, dict[tuple[str, str], _LazyTypeDescriptor]]

    def __init__(self):
        """Initialize an empty type registry."""
        self._indexed_types = dict()

    def register_type(self, type_spec: TypeSpec) -> None:
        """Register a type as atomic.

        Args:
            type_spec: The type definition to register.
        """
        # Clear cache if is_atomic_type is already defined
        if 'is_atomic_type' in globals():
            is_atomic_type.cache_clear()
        type_spec = _LazyTypeDescriptor(type_spec)
        second_key = (type_spec.module_name, type_spec.type_name)
        for first_key in [type_spec.module_name, type_spec.type_name]:
            if first_key not in self._indexed_types:
                self._indexed_types[first_key] = dict()
            self._indexed_types[first_key][second_key] = type_spec

    def register_many_types(self, types: Iterable[TypeSpec]) -> None:
        """Register multiple types as atomic."""
        for type_spec in types:
            self.register_type(type_spec)

    def is_registered(self, type_spec: TypeSpec) -> bool:
        """Check if a type is registered as atomic.

        Resolves the type specification and checks against registered descriptors.
        Robustly handles type aliases and re-exports.

        Args:
            type_spec: The type to check.

        Returns:
            True if the type is registered, False otherwise.

        Raises:
            TypeError: If the query type cannot be imported.
        """
        type_spec = _LazyTypeDescriptor(type_spec)
        query_type = type_spec.type
        if query_type is _TypeCouldNotBeImported:
            raise TypeError(f"Query type {query_type} is not allowed to be "
                            "checked if registered")

        query_root = type_spec.module_name.split('.')[0]

        for first_key in [type_spec.module_name, type_spec.type_name]:
            indexed_with_first_key = self._indexed_types.get(first_key)
            if indexed_with_first_key:
                for descriptor in indexed_with_first_key.values():
                    # Skip unloaded modules with different roots to avoid unnecessary imports
                    if descriptor.module_name not in sys.modules:
                        desc_root = descriptor.module_name.split('.')[0]
                        if query_root != desc_root:
                            continue
                    registered_type = descriptor.type
                    if registered_type is not _TypeCouldNotBeImported:
                        if registered_type is query_type:
                            return True
        return False

    def is_inherited_from_registered(self, type_spec: TypeSpec) -> bool:
        """Check if a type inherits from a registered type."""
        type_spec = _LazyTypeDescriptor(type_spec)
        query_type = type_spec.type
        if query_type is _TypeCouldNotBeImported:
            raise TypeError(f"Query type {query_type} is not allowed to be "
                            "checked if registered")

        for ancestor in query_type.__mro__:
            if self.is_registered(ancestor):
                return True
        return False


# A registry of atomic (indivisible) types.
_ATOMIC_TYPES_REGISTRY: Final[_LazyTypeRegistry] = _LazyTypeRegistry()


# Builtin types treated as atomic (not recursively flattened).
# Strings/bytes are iterable but should not be decomposed into characters/bytes.
_BUILTIN_ATOMIC_TYPES: Final[list[type]] = [
    str, bytes, bytearray, memoryview,
    int, float, complex, bool, type(None)
]

_ATOMIC_TYPES_REGISTRY.register_many_types(_BUILTIN_ATOMIC_TYPES)


# Key standard library atomics beyond builtins
_STANDARD_LIBRARY_ATOMIC_TYPES: Final[list[type]] = [
    pathlib.Path,
    pathlib.PurePath,
    datetime.datetime,
    datetime.date,
    datetime.time,
    datetime.timedelta,
    datetime.timezone,
    decimal.Decimal,
    fractions.Fraction,
    uuid.UUID,
    re.Pattern,
    enum.Enum,
    range,
]

_ATOMIC_TYPES_REGISTRY.register_many_types(
    _STANDARD_LIBRARY_ATOMIC_TYPES)


# Atomic types from popular packages
_ATOMIC_TYPES_FROM_POPULAR_PACKAGES: Final[list[tuple[str,str]]] = [
    ("numpy", "ndarray"),
    ("numpy", "generic"),
    ("numpy", "dtype"),

    ("pandas", "DataFrame"),
    ("pandas", "Series"),
    ("pandas", "Index"),
    ("pandas", "Timestamp"),
    ("pandas", "Timedelta"),

    ("polars", "DataFrame"),
    ("polars", "LazyFrame"),
    ("polars", "Series"),

    ("scipy.sparse", "spmatrix"),

    ("xarray", "DataArray"),
    ("xarray", "Dataset"),

    ("dask.array", "Array"),
    ("dask.dataframe", "DataFrame"),

    ("pyarrow", "Array"),
    ("pyarrow", "Table"),
    ("pyarrow", "RecordBatch"),

    ("cupy", "ndarray"),

    ("torch", "Tensor"),
    ("tensorflow", "Tensor"),
    ("tensorflow", "Variable"),

    ("jax.numpy", "Array"),

    ("PIL.Image", "Image"),

    ("sympy", "Basic"),

    ("networkx", "Graph"),
    ("networkx", "DiGraph"),

    ("shapely.geometry", "BaseGeometry"),

    ("astropy.units", "Quantity"),

    ("h5py", "Dataset"),
    ("h5py", "File"),

    ("pyspark.sql", "DataFrame"),
    ("pyspark.sql", "Column"),

    ("zarr.core", "Array"),
    ("zarr.hierarchy", "Group"),

    ("netCDF4", "Dataset"),
    ("netCDF4", "Variable"),

    ("Bio.Seq", "Seq"),
    ("Bio.Align", "MultipleSeqAlignment"),

    ("rdkit.Chem.rdchem", "Mol"),

    ("ipaddress", "IPv4Address"),
    ("ipaddress", "IPv6Address"),
    ("ipaddress", "IPv4Network"),
    ("ipaddress", "IPv6Network"),
]

_ATOMIC_TYPES_REGISTRY.register_many_types(
    _ATOMIC_TYPES_FROM_POPULAR_PACKAGES)

@cache
def is_atomic_type(type_to_check: type) -> bool:
    """Check if a type is atomic (indivisible).

    Args:
        type_to_check: The type to check.

    Returns:
        True if the type or any of its ancestors is registered as atomic.

    Raises:
        TypeError: If type_to_check is not a type.
    """
    if not isinstance(type_to_check, type):
        raise TypeError(f"type_to_check must be a type, got {type(type_to_check).__name__}")
    return _ATOMIC_TYPES_REGISTRY.is_inherited_from_registered(type_to_check)


def is_atomic_object(obj: object) -> bool:
    """Check if an object's type is atomic (indivisible).

    Args:
        obj: The object to check.

    Returns:
        True if the object's type is registered as atomic.
    """
    return is_atomic_type(type(obj))
