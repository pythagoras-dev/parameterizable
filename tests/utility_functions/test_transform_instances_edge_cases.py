# tests/test_transform_edge_cases.py
from dataclasses import dataclass
from collections.abc import Iterator, Mapping

from mixinforge.utility_functions.nested_collections_transformer import (
    transform_instances_inside_composite_object,
)


# --------------------------------------------------------------------------- #
# Helper targets
# --------------------------------------------------------------------------- #
@dataclass
class Target:
    name: str
    value: int


# A *frozen* (immutable) dataclass variant
@dataclass(frozen=True)
class FrozenTarget:
    name: str
    value: int


# --------------------------------------------------------------------------- #
# 1.  Iterator is consumed by the “has_target” probe
# --------------------------------------------------------------------------- #

def test_iterator_consumption_loses_elements():
    """If the root object is an *iterator*, the first traversal consumes it.
    The subsequent reconstruction therefore sees an exhausted iterator and
    fails to transform the objects that have already been yielded once.
    """
    # iterator with a single Target inside
    data: Iterator[Target] = iter([Target("solo", 1)])

    result = transform_instances_inside_composite_object(
        data,
        Target,
        lambda t: Target(t.name + "_done", t.value + 10),
    )

    # Convert the potentially transformed iterator to a list for inspection
    transformed_items = list(result)

    # We *expect* the inner Target to be modified,
    # but today the iterator is empty or still original.
    assert transformed_items == [Target("solo_done", 11)]


def test_nested_iterator_is_converted_to_list():
    """Nested iterators are converted to lists to avoid re-consumption issues.

    When an iterator is nested inside a container, the reconstruction logic
    must convert it to a list first, otherwise the iterator would be consumed
    during traversal and the constructor would receive an exhausted iterator.
    """
    nested_iter: Iterator[Target] = iter([Target("a", 1), Target("b", 2)])
    data = {"items": nested_iter}

    result = transform_instances_inside_composite_object(
        data,
        Target,
        lambda t: Target(t.name.upper(), t.value * 10),
    )

    # The nested iterator should be converted to a list with transformed items
    assert isinstance(result["items"], list)
    assert len(result["items"]) == 2
    assert result["items"][0] == Target("A", 10)
    assert result["items"][1] == Target("B", 20)


# --------------------------------------------------------------------------- #
# 2.  Frozen dataclasses cannot be replaced without unsafe=True
# --------------------------------------------------------------------------- #

def test_frozen_dataclass_transformation():
    """Verify the transformer can handle @dataclass(frozen=True) instances."""
    obj = FrozenTarget("immutable", 3)

    out = transform_instances_inside_composite_object(
        obj,
        FrozenTarget,
        lambda t: FrozenTarget(t.name, t.value + 100),
    )
    # Should return the *new* object
    assert out.value == 103
    assert out is not obj


# --------------------------------------------------------------------------- #
# 3.  Re-creating custom Mapping subclasses with non-trivial __init__
# --------------------------------------------------------------------------- #
class StrictDict(dict):
    """A dict subclass that requires an extra positional argument."""

    def __init__(self, mandatory: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mandatory = mandatory



def test_mapping_subclass_constructor_mismatch():
    inner = Target("k", 1)
    original: Mapping = StrictDict("required", {"k": inner})

    def transform(t: Target) -> Target:
        return Target(t.name, t.value + 1)

    out = transform_instances_inside_composite_object(original, Target, transform)
    # On success we should get back a *StrictDict* with transformed values
    assert isinstance(out, StrictDict)
    assert out["k"].value == 2
    assert out.mandatory == "required"


# --------------------------------------------------------------------------- #
# 4.  Multi-field dataclass reconstruction preserves field-value mapping
# --------------------------------------------------------------------------- #
@dataclass
class MultiFieldTarget:
    """Dataclass with multiple fields to verify correct field-value pairing."""
    alpha: int
    beta: str
    gamma: float


def test_dataclass_multifield_reconstruction_preserves_field_mapping():
    """Verify that multi-field dataclasses maintain correct field-value associations.

    Ensures that field values are matched by name, not by position, preventing
    silent data corruption if iteration order were to differ from field order.
    """
    inner = MultiFieldTarget(alpha=1, beta="two", gamma=3.0)
    container = {"data": inner}

    def transform(t: MultiFieldTarget) -> MultiFieldTarget:
        return MultiFieldTarget(
            alpha=t.alpha * 10,
            beta=t.beta.upper(),
            gamma=t.gamma + 0.5,
        )

    out = transform_instances_inside_composite_object(container, MultiFieldTarget, transform)

    result = out["data"]
    assert result.alpha == 10
    assert result.beta == "TWO"
    assert result.gamma == 3.5
