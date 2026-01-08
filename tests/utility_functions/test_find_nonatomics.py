"""Tests for find_nonatomics_inside_composite_object function."""
import pytest
from dataclasses import dataclass
from typing import Optional

from mixinforge.utility_functions.nested_collections_processor import find_nonatomics_inside_composite_object


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
    
    result = list(find_nonatomics_inside_composite_object(data, Target))
    assert result == [t1, t2]


def test_find_nested_objects():
    """Find target objects nested in collections."""
    t1 = Target("1")
    t2 = Target("2")
    data = {"a": [t1], "b": {"c": t2}}
    
    result = list(find_nonatomics_inside_composite_object(data, Target))
    assert result == [t1, t2]


def test_find_inside_target_objects():
    """Find target objects nested inside other target objects."""
    t1 = Target("inner")
    t2 = Target("outer", nested=t1)
    
    result = list(find_nonatomics_inside_composite_object(t2, Target))
    # Should find outer first, then inner
    assert result == [t2, t1]


def test_find_with_traverse_dict_keys():
    """Find target objects when they are keys in a dictionary."""
    t1 = Target("key")
    t2 = Target("value")
    data = {t1: t2}
    
    # Without keys traversal
    result = list(find_nonatomics_inside_composite_object(data, Target, traverse_dict_keys=False))
    assert result == [t2]
    
    # With keys traversal
    result = list(find_nonatomics_inside_composite_object(data, Target, traverse_dict_keys=True))
    # Order depends on traversal but both should be present
    assert len(result) == 2
    assert t1 in result
    assert t2 in result


def test_cycle_detection():
    """Detect cycles when searching for non-atomics."""
    c1 = Container(None)
    c2 = Container(c1)
    c1.item = c2  # Cycle c1 -> c2 -> c1
    
    with pytest.raises(ValueError, match="Cyclic reference detected"):
        list(find_nonatomics_inside_composite_object(c1, Container))


def test_deduplication_by_identity():
    """Same object yielded only once even if referenced multiple times."""
    t1 = Target("1")
    data = [t1, t1, {"a": t1}]
    
    result = list(find_nonatomics_inside_composite_object(data, Target))
    assert result == [t1]


def test_atomic_target_type_raises_error():
    """Searching for an atomic type should raise TypeError."""
    with pytest.raises(TypeError, match="target_type must be a non-atomic type"):
        list(find_nonatomics_inside_composite_object([1, 2], int))
