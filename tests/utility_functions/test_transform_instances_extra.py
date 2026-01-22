# tests/test_transform_instances_extra.py
from collections import defaultdict
from dataclasses import dataclass


from mixinforge.utility_functions.nested_collections_transformer import (
    transform_instances_inside_composite_object,
)


# --------------------------------------------------------------------------- #
# Utilities used by all scenarios
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class Target:
    name: str
    value: int


def mod(t: Target) -> Target:  # simple transform that makes the change obvious
    return Target(f"{t.name}_mod", t.value + 1)


# --------------------------------------------------------------------------- #
# 1. default_factory on defaultdict must survive reconstruction
# --------------------------------------------------------------------------- #
def test_defaultdict_factory_preserved_and_items_transformed():
    d = defaultdict(list)
    d["a"].append(Target("x", 1))

    transformed = transform_instances_inside_composite_object(d, Target, mod)

    # ‑- defaultdict must STILL be a defaultdict with the original factory
    assert isinstance(transformed, defaultdict)
    assert transformed.default_factory is list

    # ‑- Existing items must be transformed
    assert transformed["a"][0].name == "x_mod"
    assert transformed["a"][0].value == 2

    # ‑- The factory really works (would raise KeyError if it was lost)
    transformed["brand_new"]  # should create empty list silently
    assert transformed["brand_new"] == []


# --------------------------------------------------------------------------- #
# 2. attributes of a plain __dict__ based object must be reconstructed
# --------------------------------------------------------------------------- #
class Box:
    def __init__(self, item: Target) -> None:
        self.item = item


def test_plain_object_attributes_reconstructed():
    obj = Box(Target("y", 10))

    transformed = transform_instances_inside_composite_object(obj, Target, mod)

    # Returned object must be *different* (or at least have mutated attr)
    assert transformed is not obj  # expect new instance, change if in-place later
    assert transformed.item.name == "y_mod"
    assert transformed.item.value == 11


# --------------------------------------------------------------------------- #
# 3. attributes stored only in __slots__ must be reconstructed
# --------------------------------------------------------------------------- #
class SlotBox:
    __slots__ = ("item",)

    def __init__(self, item: Target) -> None:
        self.item = item


def test_slots_object_attributes_reconstructed():
    obj = SlotBox(Target("z", 100))

    transformed = transform_instances_inside_composite_object(obj, Target, mod)

    assert transformed is not obj
    assert transformed.item.name == "z_mod"
    assert transformed.item.value == 101


# --------------------------------------------------------------------------- #
# 4. Mutating items inside a *mutable* but non-list iterable (set) must work
#    and the container must remain the same concrete type.
# --------------------------------------------------------------------------- #
def test_set_mutable_iterable_handled_correctly():
    s = {Target("a", 1), Target("b", 2)}
    transformed = transform_instances_inside_composite_object(s, Target, mod)

    # Preserve concrete container type
    assert isinstance(transformed, set)

    # All items transformed
    names = {t.name for t in transformed}
    values = {t.value for t in transformed}
    assert names == {"a_mod", "b_mod"}
    assert values == {2, 3}


# --------------------------------------------------------------------------- #
# 5. Cycle safety sanity-check: an object graph with a self-reference should
#    still transform exactly once.
# --------------------------------------------------------------------------- #
def test_cycle_handling_no_infinite_recursion():
    cyclic = []
    cyclic.append(cyclic)           # self-reference
    cyclic.append(Target("self", 0))

    transformed = transform_instances_inside_composite_object(cyclic, Target, mod)

    # Structure preserved (first element points back to container)
    assert transformed[0] is transformed

    # Target transformed only once
    assert transformed[1].name == "self_mod"
    assert transformed[1].value == 1