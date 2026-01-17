"""Tests for find_nonatomics_inside_composite_object function."""
import pytest
from dataclasses import dataclass
from typing import Optional

from mixinforge.utility_functions.nested_collections_inspector import find_instances_inside_composite_object


@dataclass(frozen=True)
class Target:
    name: str
    nested: Optional['Target'] = None


@dataclass
class Container:
    item: object


def test_find_simple_objects():
    """Find target objects in a simple list."""
    t1 = Target("1")
    t2 = Target("2")
    data = [t1, "other", t2]
    
    result = list(find_instances_inside_composite_object(data, Target))
    assert result == [t1, t2]


def test_find_nested_objects():
    """Find target objects nested in collections."""
    t1 = Target("1")
    t2 = Target("2")
    data = {"a": [t1], "b": {"c": t2}}
    
    result = list(find_instances_inside_composite_object(data, Target))
    assert result == [t1, t2]


def test_find_inside_target_objects():
    """Find target objects nested inside other target objects."""
    t1 = Target("inner")
    t2 = Target("outer", nested=t1)
    
    result = list(find_instances_inside_composite_object(t2, Target))
    # Should find outer first, then inner
    assert result == [t2, t1]


def test_find_with_dict_keys():
    """Find target objects when they are keys in a dictionary."""
    t1 = Target("key")
    t2 = Target("value")
    data = {t1: t2}

    # Dict keys are always traversed
    result = list(find_instances_inside_composite_object(data, Target))
    # Order depends on traversal but both should be present
    assert len(result) == 2
    assert t1 in result
    assert t2 in result


def test_cycle_handling():
    """Handle cycles gracefully when searching for non-atomics."""
    c1 = Container(None)
    c2 = Container(c1)
    c1.item = c2  # Cycle c1 -> c2 -> c1

    # Should find both containers without raising an error
    result = list(find_instances_inside_composite_object(c1, Container))
    assert len(result) == 2
    # Use identity check with any() to avoid infinite recursion in __eq__
    assert any(obj is c1 for obj in result)
    assert any(obj is c2 for obj in result)


def test_deduplication_by_identity():
    """Same object yielded only once even if referenced multiple times."""
    t1 = Target("1")
    data = [t1, t1, {"a": t1}]

    result = list(find_instances_inside_composite_object(data, Target))
    assert result == [t1]


def test_non_type_target_raises_typeerror():
    """Raise TypeError when target_type is not a type."""
    data = [1, 2, 3]

    with pytest.raises(TypeError, match="target_type"):
        list(find_instances_inside_composite_object(data, "not_a_type"))


@pytest.mark.parametrize("invalid_target", [
    None,
    42,
    "str",
    ["list"],
    {"dict": "value"},
    lambda x: x,
])
def test_various_non_type_targets_raise_typeerror(invalid_target):
    """Various non-type values should raise TypeError."""
    data = [1, 2, 3]

    with pytest.raises(TypeError):
        list(find_instances_inside_composite_object(data, invalid_target))


def test_find_atomic_target_type():
    """Find works when target_type is an atomic type like str."""
    data = [1, "hello", 2, "world", {"key": "value"}]

    result = list(find_instances_inside_composite_object(data, str))

    assert len(result) == 4
    assert "hello" in result
    assert "world" in result
    assert "key" in result
    assert "value" in result
