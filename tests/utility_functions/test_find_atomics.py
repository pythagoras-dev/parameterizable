"""Tests for find_atomics_in_nested_collections function.

Tests the stack-based traversal of nested collections to find atomic leaf elements,
with cycle detection and partial deduplication based on object identity.
"""
import datetime
import pathlib
from collections import deque
from collections.abc import Iterator

import pytest

from mixinforge.utility_functions.nested_collections_inspector import (
    flatten_nested_collection,
    _is_traversable_collection,
)


# ============================================================================
# Tests for _is_flattenable helper
# ============================================================================


def test_is_flattenable_atomic_types():
    """Atomic types should not be flattenable."""
    assert not _is_traversable_collection("string")
    assert not _is_traversable_collection(b"bytes")
    assert not _is_traversable_collection(42)
    assert not _is_traversable_collection(3.14)
    assert not _is_traversable_collection(True)
    assert not _is_traversable_collection(None)
    assert not _is_traversable_collection(pathlib.Path("/tmp"))
    assert not _is_traversable_collection(datetime.datetime.now())


def test_is_flattenable_collections():
    """Collections should be flattenable."""
    assert _is_traversable_collection([1, 2, 3])
    assert _is_traversable_collection((1, 2, 3))
    assert _is_traversable_collection({"a": 1, "b": 2})
    assert _is_traversable_collection({1, 2, 3})


def test_is_flattenable_non_iterable():
    """Non-iterable objects should not be flattenable."""
    class NonIterable:
        pass

    assert not _is_traversable_collection(NonIterable())


# ============================================================================
# Tests for get_atomics_from_nested_collections - Basic Functionality
# ============================================================================


def test_flatten_simple_list():
    """Flatten a simple nested list structure."""
    nested = [1, [2, 3], [4, [5, 6]]]
    result = list(flatten_nested_collection(nested))
    assert result == [1, 2, 3, 4, 5, 6]


def test_flatten_simple_tuple():
    """Flatten a simple nested tuple structure."""
    nested = (1, (2, 3), (4, (5, 6)))
    result = list(flatten_nested_collection(nested))
    assert result == [1, 2, 3, 4, 5, 6]


def test_flatten_mixed_list_tuple():
    """Flatten mixed lists and tuples."""
    nested = [1, (2, [3, (4, 5)])]
    result = list(flatten_nested_collection(nested))
    assert result == [1, 2, 3, 4, 5]


def test_flatten_dictionary_includes_keys():
    """Dictionary flattening traverses both keys and values."""
    nested = {"a": 1, "b": [2, 3], "c": {"d": 4}}
    result = list(flatten_nested_collection(nested))
    # Keys "a", "b", "c" and nested key "d" are yielded along with values
    assert result == ["a", "b", "c", 1, 2, 3, "d", 4]


def test_flatten_dictionary_nested():
    """Dictionary traversal with nested structures."""
    nested = {"a": 1, "b": {"c": 2, "d": [3]}}

    result = list(flatten_nested_collection(nested))

    assert result == ["a", "b", 1, "c", "d", 2, 3]


def test_flatten_nested_dictionaries():
    """Flatten deeply nested dictionary structures."""
    nested = {
        "outer": {
            "inner": [1, 2],
            "more": {"deep": 3}
        }
    }
    result = list(flatten_nested_collection(nested))
    # Keys are traversed along with values
    assert result == ["outer", "inner", "more", 1, 2, "deep", 3]


def test_flatten_empty_list():
    """Empty list yields no elements."""
    result = list(flatten_nested_collection([]))
    assert result == []


def test_flatten_empty_dict():
    """Empty dictionary yields no elements."""
    result = list(flatten_nested_collection({}))
    assert result == []


def test_flatten_nested_empty_collections():
    """Nested empty collections yield nothing."""
    nested = [[], [[]], {}, [{}]]
    result = list(flatten_nested_collection(nested))
    assert result == []


# ============================================================================
# Tests for Atomic Type Handling
# ============================================================================


def test_strings_are_atomic():
    """Strings are treated as atomic, not decomposed into characters."""
    nested = ["hello", ["world", "foo"]]
    result = list(flatten_nested_collection(nested))
    assert result == ["hello", "world", "foo"]
    # Not ['h', 'e', 'l', 'l', 'o', ...]


def test_bytes_are_atomic():
    """Bytes and bytearray are treated as atomic."""
    nested = [b"data", [bytearray(b"more")]]
    result = list(flatten_nested_collection(nested))
    assert len(result) == 2
    assert result[0] == b"data"
    assert result[1] == bytearray(b"more")


def test_numeric_types_are_atomic():
    """Numbers are yielded as leaf values."""
    nested = [1, [2.5, [3+4j]], True]
    result = list(flatten_nested_collection(nested))
    assert result == [1, 2.5, 3+4j, True]


def test_none_is_atomic():
    """None is treated as an atomic value."""
    nested = [None, [1, None], [[None]]]
    result = list(flatten_nested_collection(nested))
    # None is a singleton, so identity deduplication means it appears once
    assert result == [None, 1]


def test_path_objects_are_atomic():
    """pathlib.Path objects are treated as atomic."""
    p1 = pathlib.Path("/tmp/file1")
    p2 = pathlib.Path("/tmp/file2")
    nested = [p1, [p2]]
    result = list(flatten_nested_collection(nested))
    assert result == [p1, p2]


def test_datetime_objects_are_atomic():
    """datetime objects are treated as atomic."""
    dt1 = datetime.datetime(2024, 1, 1)
    dt2 = datetime.date(2024, 1, 2)
    nested = [dt1, [dt2]]
    result = list(flatten_nested_collection(nested))
    assert result == [dt1, dt2]


# ============================================================================
# Tests for Partial Deduplication (Identity-Based)
# ============================================================================


def test_same_object_referenced_multiple_times_yields_once():
    """Same object (by identity) is yielded only once."""
    shared = [1, 2, 3]
    nested = [shared, shared, shared]
    result = list(flatten_nested_collection(nested))
    # shared is traversed once, not three times
    assert result == [1, 2, 3]


def test_same_atomic_object_yielded_once():
    """Same atomic object (by identity) is yielded only once."""
    obj = "shared_string"
    nested = [obj, [obj, [obj]]]
    result = list(flatten_nested_collection(nested))
    assert len(result) == 1
    assert result[0] is obj


def test_different_objects_with_same_value_all_yielded():
    """Different objects with equal values - but small ints are cached."""
    # Create separate list objects with the same content
    nested = [[1, 2], [1, 2], [1, 2]]
    result = list(flatten_nested_collection(nested))
    # Each list is a different object, but 1 and 2 are cached singletons
    # So they appear only once due to identity-based deduplication
    assert result == [1, 2]


def test_different_atomic_objects_with_same_value_all_yielded():
    """Large integers (not cached) with same value are different objects."""
    # Use large integers which aren't cached by Python
    # Create them in a way that ensures different identity
    a = int("9" * 100)
    b = int("9" * 100)
    # Verify they have the same value but different identity
    assert a == b
    if a is b:
        pytest.skip("Large integers unexpectedly have same identity")
    nested = [a, b]
    result = list(flatten_nested_collection(nested))
    assert len(result) == 2
    assert result[0] == result[1]


def test_shared_substructure_traversed_once():
    """Shared nested structure is traversed once, not repeatedly."""
    inner = [1, 2]
    middle = [inner, 3]
    nested = [middle, middle, middle]
    result = list(flatten_nested_collection(nested))
    # middle and inner are each traversed once
    assert result == [1, 2, 3]


# ============================================================================
# Tests for Cycle Detection
# ============================================================================


def test_self_referential_list_handled():
    """Self-referential list is handled gracefully."""
    cyclic = [1, 2]
    cyclic.append(cyclic)

    # Should yield atomic values without raising an error
    result = list(flatten_nested_collection(cyclic))
    assert 1 in result
    assert 2 in result


def test_circular_reference_between_lists_handled():
    """Circular reference between two lists is handled gracefully."""
    list_a = [1]
    list_b = [2, list_a]
    list_a.append(list_b)

    # Should yield atomic values without raising an error
    result = list(flatten_nested_collection(list_a))
    assert 1 in result
    assert 2 in result


def test_circular_reference_in_dict_handled():
    """Circular reference in dictionary values is handled gracefully."""
    d = {"a": 1}
    d["self"] = d

    # Should yield atomic values without raising an error
    result = list(flatten_nested_collection(d))
    # Should yield the key "a" and the value 1, and the key "self"
    assert 1 in result
    assert "a" in result
    assert "self" in result


def test_deeply_nested_cycle_handled():
    """Cycles deep in nested structures are handled gracefully."""
    inner = [1]
    middle = [inner, 2]
    outer = [middle, 3]
    inner.append(outer)  # Create cycle: inner -> middle -> outer -> inner

    # Should yield atomic values without raising an error
    result = list(flatten_nested_collection(outer))
    # Each atomic value should appear once
    assert 1 in result
    assert 2 in result
    assert 3 in result


def test_no_false_positive_cycle_with_shared_structure():
    """Shared structure (DAG) should not be mistaken for a cycle."""
    shared = [1, 2]
    nested = [[shared, shared], [shared, 3]]
    # This is a DAG, not a cycle - should work fine
    result = list(flatten_nested_collection(nested))
    assert result == [1, 2, 3]


# ============================================================================
# Tests for Error Handling
# ============================================================================


def test_non_iterable_input_raises_typeerror():
    """Non-iterable input raises TypeError."""
    with pytest.raises(TypeError):
        list(flatten_nested_collection(42))


def test_none_input_raises_typeerror():
    """None as input raises TypeError."""
    with pytest.raises(TypeError):
        list(flatten_nested_collection(None))


def test_string_as_input_is_atomic_iterable():
    """String as top-level input is rejected because strings are atomic."""
    # Strings are atomic and cannot be used as the top-level input collection
    # The function requires a non-atomic iterable as input
    with pytest.raises(TypeError):
        list(flatten_nested_collection("hello"))


# ============================================================================
# Tests for Edge Cases
# ============================================================================


def test_deeply_nested_structure():
    """Handle deeply nested structures without recursion limit issues."""
    # Create a structure nested 1000 levels deep
    nested = [1]
    for _ in range(1000):
        nested = [nested]
    result = list(flatten_nested_collection(nested))
    assert result == [1]


def test_mixed_mappings_and_sequences():
    """Handle complex mix of mappings and sequences."""
    nested = [
        {"a": [1, 2]},
        [{"b": 3}, 4],
        {"c": {"d": [5, 6]}}
    ]
    result = list(flatten_nested_collection(nested))
    # Keys are traversed along with values
    assert result == ["a", 1, 2, "b", 3, 4, "c", "d", 5, 6]


def test_sets_are_flattened():
    """Sets are iterable and should be flattened."""
    nested = [1, {2, 3}, [4]]
    result = list(flatten_nested_collection(nested))
    # Sets are unordered, so we use set comparison
    assert set(result) == {1, 2, 3, 4}
    assert len(result) == 4


def test_frozensets_are_flattened():
    """Frozensets are iterable and should be flattened."""
    nested = [1, frozenset([2, 3]), [4]]
    result = list(flatten_nested_collection(nested))
    assert set(result) == {1, 2, 3, 4}
    assert len(result) == 4


def test_range_objects_are_atomic():
    """Range objects are treated as atomic, not flattened."""
    # range is registered as an atomic type
    r1 = range(3)
    r2 = range(3, 5)
    nested = [r1, [r2]]
    result = list(flatten_nested_collection(nested))
    assert result == [r1, r2]


def test_deque_is_flattened():
    """Deque objects are iterable and should be flattened."""
    nested = [deque([1, 2]), [3, deque([4, 5])]]
    result = list(flatten_nested_collection(nested))
    assert result == [1, 2, 3, 4, 5]


def test_generator_as_input():
    """Generator as input should work correctly."""
    def gen():
        yield 1
        yield [2, 3]
        yield 4

    result = list(flatten_nested_collection(gen()))
    assert result == [1, 2, 3, 4]


def test_nested_generators():
    """Nested generators should be flattened."""
    def inner_gen():
        yield 2
        yield 3

    def outer_gen():
        yield 1
        yield inner_gen()
        yield 4

    result = list(flatten_nested_collection(outer_gen()))
    assert result == [1, 2, 3, 4]


def test_custom_iterable_class():
    """Custom iterable classes should be flattened."""
    class CustomIterable:
        def __iter__(self):
            return iter([1, 2, 3])

    nested = [CustomIterable(), [4, 5]]
    result = list(flatten_nested_collection(nested))
    assert result == [1, 2, 3, 4, 5]


def test_return_type_is_iterator():
    """Function returns an iterator, not a list."""
    nested = [1, 2, 3]
    result = flatten_nested_collection(nested)
    assert isinstance(result, Iterator)
    # Verify it's lazy by consuming it
    assert next(result) == 1
    assert next(result) == 2
    assert next(result) == 3
    with pytest.raises(StopIteration):
        next(result)


def test_multiple_none_values():
    """Multiple None values with same identity are deduplicated."""
    # None is a singleton in Python, so all None values have the same id
    nested = [None, [None, [None]]]
    result = list(flatten_nested_collection(nested))
    # All None values have the same identity, so only one is yielded
    assert result == [None]


def test_boolean_singletons():
    """Boolean singletons (True/False) are deduplicated by identity."""
    # True and False are singletons in Python
    nested = [True, [True, False], [[True, False]]]
    result = list(flatten_nested_collection(nested))
    # Each singleton appears once
    assert result == [True, False]


def test_small_integer_caching():
    """Small integers are cached by Python and deduplicated by identity."""
    # Python caches small integers (-5 to 256)
    nested = [1, [1, 2], [[1, 2, 3]]]
    result = list(flatten_nested_collection(nested))
    # Due to integer caching, each unique small int appears once
    assert result == [1, 2, 3]


def test_large_integers_not_deduplicated_by_value():
    """Large integers (different objects) are not deduplicated."""
    # Large integers are not cached, so each is a different object
    a = 10**100
    b = 10**100
    assert a == b and a is not b  # Same value, different identity
    nested = [a, b]
    result = list(flatten_nested_collection(nested))
    assert len(result) == 2
    assert result[0] == result[1] == 10**100
