"""Utilities for detecting atomic types (leaf nodes) in object trees.

This module provides mechanisms to register and detect types that should
be treated as atomic (indivisible) during traversal or flattening operations,
supporting lazy loading to avoid unnecessary imports.
"""
from __future__ import annotations
from typing import TypeAlias, Self
import importlib

TypeSpec: TypeAlias = type | "LazyTypeDescriptor" | tuple[str, str]

class _TypeCouldNotBeImported:
    """Sentinel type for types that cannot be imported."""
    pass

class LazyTypeDescriptor:
    """Defers type resolution until needed, avoiding delaying expensive imports.

    Stores type information as strings (module and type names) or as an
    actual type object. The type is resolved lazily on first access via
    the type property, which imports the module and retrieves the type.

    Attributes:
        module_name: Module name containing the type.
        type_name: Name of the type within its module.
        type: The resolved type object, importing if necessary.
    """

    _module_name: str
    _type_name: str
    _actual_type: type | None

    def __init__(self, type_spec: TypeSpec):
        """Initialize the descriptor with type information.

        Args:
            type_spec: Type specification, which can be:
                - A LazyTypeDescriptor instance (will copy its internal state)
                - A type object
                - A tuple of (module_name, type_name) strings

        Raises:
            ValueError: If tuple strings are empty or tuple has wrong length.
            TypeError: If type_spec is not a supported type.
        """
        if isinstance(type_spec, LazyTypeDescriptor):
            self._module_name = type_spec._module_name
            self._type_name = type_spec._type_name
            self._actual_type = type_spec._actual_type
        elif isinstance(type_spec, type):
            self._actual_type = type_spec
            self._module_name = type_spec.__module__
            self._type_name   = type_spec.__qualname__
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
        """The resolved type object, importing on first access.

        Returns:
            The type object, or _TypeCouldNotBeImported sentinel if import
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
        except (ImportError, AttributeError):
            self._actual_type = _TypeCouldNotBeImported

        return self._actual_type



class LazyTypeRegister:
    """Registry for types that should be treated as atomic.

    Maintains a collection of type descriptors that can be queried to check if
    an object's type is registered as atomic. Supports lazy resolution of
    types to avoid importing libraries until necessary.

    The registry uses a dual-key indexing strategy (module name and type name)
    to robustly handle aliased types and re-exports.
    """

    _indexed_types: dict[str, dict[tuple[str, str], LazyTypeDescriptor]]

    def __init__(self):
        """Initialize an empty type registry."""
        self._indexed_types =  dict()

    def register_type(self, type_spec: TypeSpec):
        """Register a type as atomic.

        Args:
            type_spec: The type to register. Can be a type object, a
                (module, name) tuple, or an existing LazyTypeDescriptor.
        """
        type_spec = LazyTypeDescriptor(type_spec)
        second_key = (type_spec.module_name, type_spec.type_name)
        for first_key in [type_spec.module_name, type_spec.type_name]:
            if first_key not in self._indexed_types:
                self._indexed_types[first_key] = dict()
            self._indexed_types[first_key][second_key] = type_spec


    def is_type_registered(self, type_spec: TypeSpec) -> bool:
        """Check if a type is registered as atomic.

        Resolves the type specification and checks against registered descriptors.
        Handles type aliases by checking if the underlying type object matches
        any registered descriptor found by name or module.

        Args:
            type_spec: The type to check.

        Returns:
            True if the type is registered as atomic, False otherwise.
        """
        type_spec = LazyTypeDescriptor(type_spec)
        for first_key in [type_spec.module_name, type_spec.type_name]:
            indexed_with_first_key = self._indexed_types.get(first_key)
            if indexed_with_first_key:
                for descriptor in indexed_with_first_key.values():
                    registered_type = descriptor.type
                    if registered_type is not _TypeCouldNotBeImported:
                        if registered_type == type_spec.type:
                            return True
        return False

    def __contains__(self, type_spec: TypeSpec) -> bool:
        """Check if a type is in the registry.

        Alias for is_type_registered.
        """
        return self.is_type_registered(type_spec)

    def __iadd__(self, type_spec: TypeSpec) -> Self:
        """Register a type using the += operator.

        Args:
            type_spec: The type to register.

        Returns:
            Self: The registry instance.
        """
        self.register_type(type_spec)
        return self
