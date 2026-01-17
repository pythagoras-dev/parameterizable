"""Ensure transform keeps the *exact* defaultdict subclass and its factory."""

from collections import defaultdict
from dataclasses import dataclass

from mixinforge.utility_functions.nested_collections_transformer import (
    transform_instances_inside_composite_object,
)


# --------------------------------------------------------------------------- #
# Shared test helpers
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class Target:
    name: str
    value: int


def mod(t: Target) -> Target:
    """Simple transformation used in all tests."""
    return Target(f"{t.name}_mod", t.value + 42)


# --------------------------------------------------------------------------- #
# Custom defaultdict subclass used to reproduce the issue
# --------------------------------------------------------------------------- #
class CustomDD(defaultdict):
    """Adds one trivial attribute so identity loss is obvious."""
    def __init__(self):
        super().__init__(list)
        self.extra_attr = "present"


# --------------------------------------------------------------------------- #
# Test case
# --------------------------------------------------------------------------- #
def test_defaultdict_subclass_and_factory_survive_transformation():
    original = CustomDD()
    original["key"].append(Target("a", 1))

    transformed = transform_instances_inside_composite_object(original, Target, mod)

    # -- The concrete subclass must be preserved
    assert isinstance(transformed, CustomDD)

    # -- Its extra attribute must still be there
    assert getattr(transformed, "extra_attr", None) == "present"

    # -- Factory must remain *list*
    assert transformed.default_factory is list

    # -- Contents must be transformed
    assert transformed["key"][0].name == "a_mod"
    assert transformed["key"][0].value == 43

    # -- Factory still works
    transformed["new_key"]          # should auto-create via default_factory
    assert transformed["new_key"] == []