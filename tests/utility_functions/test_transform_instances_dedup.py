"""Tests for transform deduplication guarantee.

Verifies that transform_instances_inside_composite_object calls the transform
function exactly once per unique object instance, regardless of how many times
that instance appears in the structure.
"""
from mixinforge import transform_instances_inside_composite_object


class Target:
    """Target class for transformation."""

    def __init__(self, value: int):
        self.value = value


class Container:
    """Container class that holds targets."""

    def __init__(self, target: Target):
        self.target = target


def test_transform_called_once_per_unique_instance():
    """Verify transform function is called exactly once per unique instance."""
    call_log = []

    def counting_transform(obj):
        call_log.append(id(obj))
        return Target(obj.value * 2)

    # Same instance referenced multiple times in a list
    shared = Target(10)
    structure = [shared, shared, shared]

    result = transform_instances_inside_composite_object(
        structure, Target, counting_transform
    )

    # Transform should be called exactly once
    assert len(call_log) == 1
    assert call_log[0] == id(shared)

    # All references should point to same transformed instance
    assert result[0] is result[1] is result[2]
    assert result[0].value == 20


def test_transform_dedup_with_nested_structure():
    """Verify dedup works with nested structures containing same instance."""
    call_count = [0]

    def counting_transform(obj):
        call_count[0] += 1
        return Target(obj.value + 100)

    shared = Target(5)
    structure = {
        "a": shared,
        "b": [shared, {"nested": shared}],
        "c": (shared,),
    }

    result = transform_instances_inside_composite_object(
        structure, Target, counting_transform
    )

    # Called only once despite 4 references
    assert call_count[0] == 1

    # All point to same transformed instance
    transformed = result["a"]
    assert result["b"][0] is transformed
    assert result["b"][1]["nested"] is transformed
    assert result["c"][0] is transformed
    assert transformed.value == 105


def test_transform_dedup_multiple_unique_instances():
    """Verify each unique instance is transformed exactly once."""
    transform_calls = {}

    def counting_transform(obj):
        obj_id = id(obj)
        transform_calls[obj_id] = transform_calls.get(obj_id, 0) + 1
        return Target(obj.value * 10)

    target1 = Target(1)
    target2 = Target(2)
    target3 = Target(3)

    # Each target appears multiple times
    structure = [
        target1,
        target2,
        target1,
        target3,
        target2,
        target1,
        target3,
    ]

    result = transform_instances_inside_composite_object(
        structure, Target, counting_transform
    )

    # Each unique instance called exactly once
    assert len(transform_calls) == 3
    assert all(count == 1 for count in transform_calls.values())

    # Verify same transformed instances are reused
    assert result[0] is result[2] is result[5]  # target1 refs
    assert result[1] is result[4]  # target2 refs
    assert result[3] is result[6]  # target3 refs


def test_transform_dedup_in_object_attributes():
    """Verify dedup works when same instance is in multiple object attributes."""
    call_count = [0]

    def counting_transform(obj):
        call_count[0] += 1
        return Target(obj.value + 1)

    shared = Target(42)
    container1 = Container(shared)
    container2 = Container(shared)

    structure = [container1, container2]

    result = transform_instances_inside_composite_object(
        structure, Target, counting_transform
    )

    # Transform called once for the shared target
    assert call_count[0] == 1

    # Both containers now reference same transformed instance
    assert result[0].target is result[1].target
    assert result[0].target.value == 43


def test_transform_dedup_with_cycles():
    """Verify dedup works correctly with cyclic structures."""
    call_count = [0]

    def counting_transform(obj):
        call_count[0] += 1
        result = Target(obj.value * 2)
        return result

    target = Target(7)
    structure = [target]
    structure.append(structure)  # Create cycle

    result = transform_instances_inside_composite_object(
        structure, Target, counting_transform
    )

    # Transform called exactly once for the target
    assert call_count[0] == 1
    assert result[0].value == 14


def test_transform_dedup_dict_key_and_value():
    """Verify dedup works when same instance is both dict key and value."""
    call_count = [0]

    class HashableTarget:
        """Hashable target for use as dict key."""

        def __init__(self, value: int):
            self.value = value

        def __hash__(self):
            return hash(self.value)

        def __eq__(self, other):
            return isinstance(other, HashableTarget) and self.value == other.value

    def counting_transform(obj):
        call_count[0] += 1
        return HashableTarget(obj.value * 3)

    shared = HashableTarget(10)

    # Same instance as both key and value
    structure = {shared: shared}

    result = transform_instances_inside_composite_object(
        structure, HashableTarget, counting_transform
    )

    # Should be called only once
    assert call_count[0] == 1

    # The transformed instance should be used for both key and value
    keys = list(result.keys())
    values = list(result.values())
    assert len(keys) == 1
    assert keys[0] is values[0]
    assert keys[0].value == 30


def test_transform_dedup_set_elements():
    """Verify dedup tracking works even though sets deduplicate by equality."""
    call_ids = []

    def counting_transform(obj):
        call_ids.append(id(obj))
        return Target(obj.value + 5)

    t1 = Target(1)
    t2 = Target(2)

    # Set with two different targets
    structure = {t1, t2}

    transform_instances_inside_composite_object(
        structure, Target, counting_transform)

    # Each unique instance transformed once
    assert len(call_ids) == 2
    assert len(set(call_ids)) == 2  # All unique IDs


def test_transform_dedup_preserves_identity_in_result():
    """Verify that identity relationships are preserved in the result."""
    transform_map = {}

    def tracking_transform(obj):
        result = Target(obj.value * 2)
        transform_map[id(obj)] = result
        return result

    shared = Target(10)
    unique = Target(20)

    structure = {
        "shared1": shared,
        "shared2": shared,
        "unique": unique,
    }

    result = transform_instances_inside_composite_object(
        structure, Target, tracking_transform
    )

    # Shared references map to same transformed instance
    assert result["shared1"] is result["shared2"]

    # Unique is different
    assert result["unique"] is not result["shared1"]

    # Values are correct
    assert result["shared1"].value == 20
    assert result["unique"].value == 40
