"""Tests for internal traversal logic (slots, dicts, properties)."""
import pytest
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

from mixinforge.utility_functions.nested_collections_processor import find_nonatomics_inside_composite_object


@dataclass(frozen=True)
class Leaf:
    value: int


class SlotsOnly:
    __slots__ = ('a', 'b')

    def __init__(self, a, b):
        self.a = a
        self.b = b


class SlotsParent:
    __slots__ = ('parent_attr',)

    def __init__(self, val):
        self.parent_attr = val


class SlotsChild(SlotsParent):
    __slots__ = ('child_attr',)

    def __init__(self, p_val, c_val):
        super().__init__(p_val)
        self.child_attr = c_val


class MixedSlotsDict(SlotsParent):
    # No __slots__ defined here, so it has __dict__
    # Inherits __slots__ from SlotsParent
    pass


class WithProperties:
    def __init__(self, val):
        self._val = val

    @property
    def prop(self):
        # Should not be traversed/executed
        raise RuntimeError("Property accessed!")

    @property
    def val(self):
        return self._val


class UninitializedSlots:
    __slots__ = ('a', 'b')

    def __init__(self, a):
        self.a = a
        # b is left uninitialized


class IterableWithAttrs(list):
    def __init__(self, items, extra):
        super().__init__(items)
        self.extra = extra


class CustomMapping(Mapping):
    def __init__(self, data, extra):
        self._data = data
        self.extra = extra

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


def find_leaves(obj: Any, traverse_dict_keys: bool = False) -> list[int]:
    """Helper to find Leaf objects and return their values."""
    # We search for Leaf objects.
    # traverse_dict_keys is passed through.
    found = find_nonatomics_inside_composite_object(obj, Leaf, traverse_dict_keys=traverse_dict_keys)
    return sorted(leaf.value for leaf in found)


def test_traverse_slots_only():
    """Verify traversal of objects with __slots__."""
    obj = SlotsOnly(Leaf(1), [Leaf(2)])
    result = find_leaves(obj)
    assert result == [1, 2]


def test_traverse_inherited_slots():
    """Verify traversal of inherited __slots__."""
    obj = SlotsChild(Leaf(1), Leaf(2))
    result = find_leaves(obj)
    assert result == [1, 2]


def test_traverse_mixed_slots_and_dict():
    """Verify traversal of objects with both __slots__ (inherited) and __dict__."""
    obj = MixedSlotsDict(Leaf(1))
    obj.dynamic = Leaf(2)
    result = find_leaves(obj)
    assert result == [1, 2]


def test_properties_are_skipped():
    """Verify that properties are not accessed during traversal."""
    obj = WithProperties(Leaf(1))
    # If property is accessed, RuntimeError would be raised
    result = find_leaves(obj)
    # Only _val (via __dict__) should be traversed
    assert result == [1]


def test_uninitialized_slots_are_skipped():
    """Verify that uninitialized slots do not cause errors."""
    obj = UninitializedSlots(Leaf(1))
    result = find_leaves(obj)
    assert result == [1]


def test_traverse_dict_keys_in_mapping():
    """Verify traverse_dict_keys=True includes keys."""
    data = {Leaf(1): Leaf(2)}
    result = find_leaves(data, traverse_dict_keys=True)
    assert result == [1, 2]


def test_traverse_dict_keys_in_mixed_structure():
    """Verify traverse_dict_keys=True propagates to nested structures."""
    data = [{"k": Leaf(1)}, {Leaf(2): "v"}]
    # keys in the first dict is string "k", value is Leaf(1) -> found 1
    # keys in second dict is Leaf(2), value is string "v" -> found 2 if keys traversed
    result = find_leaves(data, traverse_dict_keys=True)
    assert result == [1, 2]


def test_iterable_subclass_attributes_and_items_traversed():
    """Iterable subclasses traverse both stored attributes and iterated items."""
    obj = IterableWithAttrs([Leaf(1)], Leaf(2))

    result = find_leaves(obj)

    assert result == [1, 2]


def test_custom_mapping_traverses_attributes_and_keys():
    """Custom mappings traverse attributes plus keys/values when requested."""
    data = {Leaf(1): Leaf(2)}
    obj = CustomMapping(data, extra=Leaf(3))

    result = find_leaves(obj, traverse_dict_keys=True)

    assert result == [1, 2, 3]
