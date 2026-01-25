"""Tests for ImmutableMixin pickling behavior.

These tests verify that ImmutableMixin's cached_property mechanism for identity_key
remains valid after unpickling and that _init_finished is properly restored.
"""
import pickle

from mixinforge import ImmutableMixin


class PicklableImmutable(ImmutableMixin):
    """Immutable class for pickling tests."""

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def get_identity_key(self):
        return self.name

    def __getstate__(self):
        # Exclude _init_finished from state (GuardedInitMeta requirement)
        state = self.__dict__.copy()
        state.pop("_init_finished", None)
        return state


class TupleKeyImmutable(ImmutableMixin):
    """Immutable with tuple identity key for testing complex keys."""

    def __init__(self, x: int, y: int):
        super().__init__()
        self.x = x
        self.y = y

    def get_identity_key(self):
        return (self.x, self.y)

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("_init_finished", None)
        return state


def test_unpickled_immutable_has_valid_identity_key():
    """Verify identity_key accessor works after unpickling."""
    original = PicklableImmutable("test")
    original_key = original.identity_key  # Cache it

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    assert restored.identity_key == original_key
    assert restored.identity_key == "test"


def test_unpickled_immutable_hashable():
    """Verify __hash__ works after unpickling."""
    original = PicklableImmutable("test")
    original_hash = hash(original)

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    assert hash(restored) == original_hash


def test_unpickled_immutable_equality():
    """Verify __eq__ works correctly after unpickling."""
    original = PicklableImmutable("test")

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    # Restored should equal original
    assert restored == original
    assert original == restored


def test_init_finished_restored():
    """Verify _init_finished is True after unpickling."""
    original = PicklableImmutable("test")
    assert original._init_finished is True

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    assert restored._init_finished is True


def test_unpickled_immutable_usable_as_dict_key():
    """Verify unpickled immutable can be used as dictionary key."""
    original = PicklableImmutable("test")
    d = {original: "value"}

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    # Should be able to access via restored key
    assert d[restored] == "value"


def test_unpickled_immutable_usable_in_set():
    """Verify unpickled immutable works correctly in sets."""
    original = PicklableImmutable("test")
    s = {original}

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    assert restored in s


def test_tuple_identity_key_preserved():
    """Verify tuple identity keys work after unpickling."""
    original = TupleKeyImmutable(1, 2)
    original_key = original.identity_key

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    assert restored.identity_key == original_key
    assert restored.identity_key == (1, 2)
    assert hash(restored) == hash(original)


def test_cached_property_regenerates_after_unpickle():
    """Verify identity_key cached_property regenerates correctly.

    The cached_property may not survive pickling, but should regenerate
    on first access after unpickling.
    """
    original = PicklableImmutable("cached_test")
    # Access to cache it
    _ = original.identity_key

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    # Whether cached or regenerated, should work correctly
    assert restored.identity_key == "cached_test"
    # Multiple accesses should return same value
    assert restored.identity_key == restored.identity_key


def test_multiple_pickle_cycles():
    """Verify multiple pickle/unpickle cycles preserve functionality."""
    original = PicklableImmutable("multi")

    # First cycle
    data1 = pickle.dumps(original)
    restored1 = pickle.loads(data1)

    # Second cycle
    data2 = pickle.dumps(restored1)
    restored2 = pickle.loads(data2)

    # All should be equal and hashable
    assert original == restored1 == restored2
    assert hash(original) == hash(restored1) == hash(restored2)
    assert restored2._init_finished is True
