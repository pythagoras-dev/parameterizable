"""Tests for internal traversal logic (slots, dicts, properties)."""
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

from mixinforge.utility_functions.nested_collections_inspector import find_instances_inside_composite_object


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


def find_leaves(obj: Any) -> list[int]:
    """Helper to find Leaf objects and return their values."""
    # We search for Leaf objects.
    found = find_instances_inside_composite_object(obj, Leaf)
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
    """Verify that dict keys are traversed."""
    data = {Leaf(1): Leaf(2)}
    result = find_leaves(data)
    assert result == [1, 2]


def test_traverse_dict_keys_in_mixed_structure():
    """Verify dict keys are traversed in nested structures."""
    data = [{"k": Leaf(1)}, {Leaf(2): "v"}]
    # keys in the first dict is string "k", value is Leaf(1) -> found 1
    # keys in second dict is Leaf(2), value is string "v" -> found 2 since keys are traversed
    result = find_leaves(data)
    assert result == [1, 2]


def test_iterable_subclass_attributes_and_items_traversed():
    """Iterable subclasses traverse both stored attributes and iterated items."""
    obj = IterableWithAttrs([Leaf(1)], Leaf(2))

    result = find_leaves(obj)

    assert result == [1, 2]


def test_custom_mapping_traverses_attributes_and_keys():
    """Custom mappings traverse attributes plus keys/values."""
    data = {Leaf(1): Leaf(2)}
    obj = CustomMapping(data, extra=Leaf(3))

    result = find_leaves(obj)

    assert result == [1, 2, 3]


# ==============================================================================
# Tests for deep_search parameter
# ==============================================================================

@dataclass
class Target:
    name: str
    value: int = 0
    nested: "Target | None" = None


def test_shallow_search_stops_at_nested_target():
    """With deep_search=False, nested targets inside matched instances are not yielded."""
    inner = Target("inner", 1)
    outer = Target("outer", 2, nested=inner)

    result = list(find_instances_inside_composite_object(outer, Target, deep_search=False))

    # Only outer should be found, inner should NOT be yielded
    assert len(result) == 1
    assert result[0].name == "outer"


def test_shallow_search_traverses_non_target_containers():
    """With deep_search=False, targets in non-target containers (dicts, lists) are still found."""
    t1 = Target("first", 1)
    t2 = Target("second", 2)
    data = {"a": t1, "b": [t2]}

    result = list(find_instances_inside_composite_object(data, Target, deep_search=False))

    # Both targets should be found (they are in non-target containers)
    assert len(result) == 2
    names = {t.name for t in result}
    assert names == {"first", "second"}


def test_shallow_search_multilevel_nesting():
    """With deep_search=False, only the outermost target is yielded."""
    level3 = Target("level3", 3)
    level2 = Target("level2", 2, nested=level3)
    level1 = Target("level1", 1, nested=level2)

    result = list(find_instances_inside_composite_object(level1, Target, deep_search=False))

    # Only level1 should be found
    assert len(result) == 1
    assert result[0].name == "level1"


def test_shallow_search_sibling_targets_in_container():
    """With deep_search=False, sibling targets in a container are all found."""
    inner1 = Target("inner1", 1)
    inner2 = Target("inner2", 2)
    outer1 = Target("outer1", 10, nested=inner1)
    outer2 = Target("outer2", 20, nested=inner2)
    data = [outer1, outer2]

    result = list(find_instances_inside_composite_object(data, Target, deep_search=False))

    # Both outer targets are found (they are siblings in the list)
    # But their nested children are NOT found
    assert len(result) == 2
    names = {t.name for t in result}
    assert names == {"outer1", "outer2"}


def test_shallow_search_mixed_containers():
    """With deep_search=False, traversal continues through all non-target container types."""
    nested_target = Target("nested", 1)
    outer_target = Target("outer", 2, nested=nested_target)
    data = {"dict": [{"inner_dict": (outer_target,)}]}

    result = list(find_instances_inside_composite_object(data, Target, deep_search=False))

    # Outer target found, nested target NOT found
    assert len(result) == 1
    assert result[0].name == "outer"


def test_deep_search_default_is_true():
    """Verify default behavior with no deep_search argument matches deep_search=True."""
    inner = Target("inner", 1)
    outer = Target("outer", 2, nested=inner)

    result_default = list(find_instances_inside_composite_object(outer, Target))
    result_explicit = list(find_instances_inside_composite_object(outer, Target, deep_search=True))

    # Both should find outer and inner
    assert len(result_default) == 2
    assert len(result_explicit) == 2
    default_names = {t.name for t in result_default}
    explicit_names = {t.name for t in result_explicit}
    assert default_names == {"outer", "inner"}
    assert explicit_names == {"outer", "inner"}
