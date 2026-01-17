"""Tests for atomics_detector module.

Tests the type registration and detection mechanisms for atomic (indivisible)
types in object traversal operations.
"""
import datetime
import pathlib
import sys
from enum import Enum

import pytest

from mixinforge.utility_functions.atomics_detector import (
    _LazyTypeDescriptor,
    _LazyTypeRegistry,
    _TypeCouldNotBeImported,
    is_atomic_type,
    is_atomic_object,
)


# ============================================================================
# Tests for _LazyTypeDescriptor
# ============================================================================


def test_lazy_type_descriptor_init_from_type():
    """Initialize descriptor from a type object."""
    descriptor = _LazyTypeDescriptor(str)

    assert descriptor.module_name == "builtins"
    assert descriptor.type_name == "str"
    assert descriptor.type is str


def test_lazy_type_descriptor_init_from_tuple():
    """Initialize descriptor from (module_name, type_name) tuple."""
    descriptor = _LazyTypeDescriptor(("pathlib", "Path"))

    assert descriptor.module_name == "pathlib"
    assert descriptor.type_name == "Path"
    assert descriptor.type is pathlib.Path


def test_lazy_type_descriptor_init_from_another_descriptor():
    """Initialize descriptor from another LazyTypeDescriptor."""
    original = _LazyTypeDescriptor(int)
    copy = _LazyTypeDescriptor(original)

    assert copy.module_name == original.module_name
    assert copy.type_name == original.type_name
    assert copy.type is int


def test_lazy_type_descriptor_invalid_tuple_length():
    """Raise ValueError for tuple with wrong number of elements."""
    with pytest.raises(ValueError):
        _LazyTypeDescriptor(("module",))

    with pytest.raises(ValueError):
        _LazyTypeDescriptor(("module", "type", "extra"))


def test_lazy_type_descriptor_empty_strings_in_tuple():
    """Raise ValueError for empty module or type name."""
    with pytest.raises(ValueError):
        _LazyTypeDescriptor(("", "SomeType"))

    with pytest.raises(ValueError):
        _LazyTypeDescriptor(("some.module", ""))


def test_lazy_type_descriptor_invalid_type_spec():
    """Raise TypeError for unsupported type_spec."""
    with pytest.raises(TypeError):
        _LazyTypeDescriptor("not_a_valid_spec")

    with pytest.raises(TypeError):
        _LazyTypeDescriptor(123)


def test_lazy_type_descriptor_import_failure():
    """Return sentinel type when import fails."""
    descriptor = _LazyTypeDescriptor(("nonexistent.module", "FakeType"))

    assert descriptor.module_name == "nonexistent.module"
    assert descriptor.type_name == "FakeType"
    assert descriptor.type is _TypeCouldNotBeImported


def test_lazy_type_descriptor_nested_class_name():
    """Handle nested class names with dots correctly."""
    # Create a nested class for testing
    class Outer:
        class Inner:
            pass

    descriptor = _LazyTypeDescriptor(Outer.Inner)

    # The type_name contains the full qualified name including locals
    assert "Outer.Inner" in descriptor.type_name
    assert descriptor.type is Outer.Inner


def test_lazy_type_descriptor_lazy_resolution():
    """Type resolution happens lazily on first access."""
    descriptor = _LazyTypeDescriptor(("datetime", "datetime"))

    # Before accessing .type, it should be None (not yet resolved)
    assert descriptor._actual_type is None

    # After accessing .type, it should be resolved
    resolved_type = descriptor.type
    assert resolved_type is datetime.datetime
    assert descriptor._actual_type is datetime.datetime

    # Subsequent accesses return cached value
    assert descriptor.type is resolved_type


# ============================================================================
# Tests for _LazyTypeRegistry
# ============================================================================


def test_lazy_type_registry_register_single_type():
    """Register a single type and verify it's detected."""
    registry = _LazyTypeRegistry()

    class CustomType:
        pass

    registry.register_type(CustomType)

    assert registry.is_registered(CustomType)


def test_lazy_type_registry_register_multiple_types():
    """Register multiple types at once."""
    registry = _LazyTypeRegistry()

    class TypeA:
        pass

    class TypeB:
        pass

    registry.register_many_types([TypeA, TypeB])

    assert registry.is_registered(TypeA)
    assert registry.is_registered(TypeB)


def test_lazy_type_registry_is_registered_with_tuple_spec():
    """Check registration using tuple specification."""
    registry = _LazyTypeRegistry()
    registry.register_type(("pathlib", "Path"))

    assert registry.is_registered(pathlib.Path)
    assert registry.is_registered(("pathlib", "Path"))


def test_lazy_type_registry_is_inherited_from_registered():
    """Detect types that inherit from registered types."""
    registry = _LazyTypeRegistry()

    class BaseType:
        pass

    class DerivedType(BaseType):
        pass

    registry.register_type(BaseType)

    assert registry.is_inherited_from_registered(BaseType)
    assert registry.is_inherited_from_registered(DerivedType)


def test_lazy_type_registry_unregistered_type_returns_false():
    """Unregistered types should return False."""
    registry = _LazyTypeRegistry()

    class UnregisteredType:
        pass

    assert not registry.is_registered(UnregisteredType)
    assert not registry.is_inherited_from_registered(UnregisteredType)


def test_lazy_type_registry_query_with_unimportable_type():
    """Raise TypeError when querying with unimportable type."""
    registry = _LazyTypeRegistry()

    with pytest.raises(TypeError):
        registry.is_registered(("fake.module", "FakeType"))

    with pytest.raises(TypeError):
        registry.is_inherited_from_registered(("fake.module", "FakeType"))


# ============================================================================
# Tests for public API: is_atomic_type
# ============================================================================


def test_is_atomic_type_builtins():
    """Builtin types should be atomic."""
    assert is_atomic_type(str)
    assert is_atomic_type(int)
    assert is_atomic_type(float)
    assert is_atomic_type(bool)
    assert is_atomic_type(bytes)
    assert is_atomic_type(type(None))


def test_is_atomic_type_stdlib_types():
    """Standard library types should be atomic."""
    assert is_atomic_type(pathlib.Path)
    assert is_atomic_type(pathlib.PurePath)
    assert is_atomic_type(datetime.datetime)
    assert is_atomic_type(datetime.date)
    assert is_atomic_type(datetime.time)


def test_is_atomic_type_with_inheritance():
    """Custom types inheriting from atomic types should be atomic."""
    class CustomPath(pathlib.Path):
        pass

    class CustomEnum(Enum):
        VALUE = 1

    assert is_atomic_type(CustomPath)
    assert is_atomic_type(CustomEnum)


def test_is_atomic_type_non_atomic_types():
    """Non-atomic types should return False."""
    assert not is_atomic_type(list)
    assert not is_atomic_type(dict)
    assert not is_atomic_type(set)
    assert not is_atomic_type(tuple)

    class CustomClass:
        pass

    assert not is_atomic_type(CustomClass)


def test_is_atomic_type_caching():
    """Verify is_atomic_type uses caching for performance."""
    # Clear cache to start fresh
    is_atomic_type.cache_clear()
    cache_info_before = is_atomic_type.cache_info()

    # First call - cache miss
    is_atomic_type(str)
    cache_info_after_first = is_atomic_type.cache_info()
    assert cache_info_after_first.misses == cache_info_before.misses + 1

    # Second call - cache hit
    is_atomic_type(str)
    cache_info_after_second = is_atomic_type.cache_info()
    assert cache_info_after_second.hits == cache_info_after_first.hits + 1


def test_is_atomic_type_cache_cleared_on_registration():
    """Cache should be cleared when new types are registered."""
    from mixinforge.utility_functions.atomics_detector import _ATOMIC_TYPES_REGISTRY

    is_atomic_type.cache_clear()

    class NewType:
        pass

    # Check before registration
    result_before = is_atomic_type(NewType)
    assert not result_before

    # Register and verify cache was cleared
    _ATOMIC_TYPES_REGISTRY.register_type(NewType)

    # After registration, should be detected as atomic
    result_after = is_atomic_type(NewType)
    assert result_after


# ============================================================================
# Tests for public API: is_atomic_object
# ============================================================================


def test_is_atomic_object_with_builtin_instances():
    """Instances of builtin types should be atomic."""
    assert is_atomic_object("hello")
    assert is_atomic_object(42)
    assert is_atomic_object(3.14)
    assert is_atomic_object(True)
    assert is_atomic_object(b"bytes")
    assert is_atomic_object(None)


def test_is_atomic_object_with_stdlib_instances():
    """Instances of stdlib types should be atomic."""
    assert is_atomic_object(pathlib.Path("/tmp"))
    assert is_atomic_object(datetime.datetime.now())
    assert is_atomic_object(datetime.date.today())


def test_is_atomic_object_with_non_atomic_instances():
    """Instances of non-atomic types should return False."""
    assert not is_atomic_object([1, 2, 3])
    assert not is_atomic_object({"key": "value"})
    assert not is_atomic_object({1, 2, 3})
    assert not is_atomic_object((1, 2, 3))

    class CustomClass:
        pass

    assert not is_atomic_object(CustomClass())


# ============================================================================
# Tests for custom type registration workflow
# ============================================================================


def test_custom_type_registration_workflow():
    """Test complete workflow of registering and detecting custom types."""
    from mixinforge.utility_functions.atomics_detector import _ATOMIC_TYPES_REGISTRY

    class MyCustomType:
        pass

    # Before registration
    assert not is_atomic_type(MyCustomType)
    assert not is_atomic_object(MyCustomType())

    # Register
    _ATOMIC_TYPES_REGISTRY.register_type(MyCustomType)

    # After registration
    assert is_atomic_type(MyCustomType)
    assert is_atomic_object(MyCustomType())

    # Subclasses should also be atomic
    class MyDerivedType(MyCustomType):
        pass

    assert is_atomic_type(MyDerivedType)
    assert is_atomic_object(MyDerivedType())


# ============================================================================
# Tests for third-party types (may not be installed)
# ============================================================================


def test_third_party_types_lazy_loading():
    """Third-party types should be checked without importing if not needed."""
    from mixinforge.utility_functions.atomics_detector import _ATOMIC_TYPES_REGISTRY

    # Register numpy ndarray (may not be installed)
    _ATOMIC_TYPES_REGISTRY.register_type(("numpy", "ndarray"))

    # If numpy is not installed, the type won't be imported yet
    # This shouldn't raise an error during registration

    # Try to check if numpy is available
    if "numpy" in sys.modules or _can_import("numpy"):
        import numpy as np
        # If numpy is available, it should be detected as atomic
        assert is_atomic_type(np.ndarray)
        assert is_atomic_object(np.array([1, 2, 3]))


def test_third_party_type_aliases():
    """Handle type aliases and re-exports correctly."""
    from mixinforge.utility_functions.atomics_detector import _ATOMIC_TYPES_REGISTRY

    # pathlib.Path is actually pathlib.PosixPath or pathlib.WindowsPath
    # Both should be detected as atomic due to inheritance
    _ATOMIC_TYPES_REGISTRY.register_type(pathlib.PurePath)

    assert is_atomic_type(pathlib.Path)
    assert is_atomic_object(pathlib.Path("/tmp"))


# ============================================================================
# Edge cases
# ============================================================================


@pytest.mark.parametrize("atomic_type,instance", [
    (str, "text"),
    (int, 42),
    (float, 3.14),
    (bool, True),
    (bytes, b"data"),
    (pathlib.Path, pathlib.Path("/")),
    (datetime.datetime, datetime.datetime.now()),
])
def test_parametrized_atomic_types(atomic_type, instance):
    """Test various atomic types with parametrization."""
    assert is_atomic_type(atomic_type)
    assert is_atomic_object(instance)


def test_type_with_complex_module_path():
    """Handle types with complex module paths."""
    # datetime.timezone is a type in datetime module
    from datetime import timezone

    assert is_atomic_type(timezone)
    assert is_atomic_object(timezone.utc)


def test_range_type_is_atomic():
    """range objects should be atomic despite being iterable."""
    assert is_atomic_type(range)
    assert is_atomic_object(range(10))


def test_strings_are_atomic_despite_being_iterable():
    """Strings should be atomic even though they're iterable."""
    # This is a critical behavior: strings shouldn't be decomposed
    assert is_atomic_type(str)
    assert is_atomic_object("hello")
    assert is_atomic_type(bytes)
    assert is_atomic_object(b"hello")


# ============================================================================
# Tests for input validation
# ============================================================================


def test_is_atomic_type_non_type_raises_typeerror():
    """Raise TypeError when is_atomic_type receives a non-type argument."""
    is_atomic_type.cache_clear()
    with pytest.raises(TypeError, match="type_to_check"):
        is_atomic_type("not_a_type")


@pytest.mark.parametrize("invalid_input", [
    None,
    42,
    "str",
    ["list"],
    {"dict": "value"},
    3.14,
])
def test_is_atomic_type_various_non_types_raise_typeerror(invalid_input):
    """Various non-type values should raise TypeError."""
    is_atomic_type.cache_clear()
    with pytest.raises(TypeError):
        is_atomic_type(invalid_input)


# ============================================================================
# Helper functions
# ============================================================================


def _can_import(module_name: str) -> bool:
    """Check if a module can be imported without actually importing it."""
    try:
        import importlib.util
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False
