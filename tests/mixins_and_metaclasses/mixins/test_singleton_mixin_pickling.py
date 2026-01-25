"""Tests for SingletonMixin pickling behavior.

These tests verify the singleton pattern is preserved through pickle/unpickle cycles.
A common failure mode for Python Singletons is that unpickling creates a distinct
instance, breaking the pattern.
"""
import pickle

from mixinforge import SingletonMixin


class PicklableSingleton(SingletonMixin):
    """Singleton class for pickling tests."""

    def __init__(self, value: int = 42):
        super().__init__()
        self.value = value


class AnotherPicklableSingleton(SingletonMixin):
    """Another singleton to test per-class isolation."""

    def __init__(self, name: str = "default"):
        super().__init__()
        self.name = name


def test_unpickled_singleton_is_same_instance():
    """Verify unpickling returns the same singleton instance.

    This is a critical test: if unpickling creates a new instance,
    the singleton pattern is broken.
    """
    original = PicklableSingleton()
    data = pickle.dumps(original)
    restored = pickle.loads(data)

    assert restored is original
    assert id(restored) == id(original)


def test_singleton_state_preserved_after_pickle():
    """Verify singleton state is preserved through pickle cycle."""
    original = PicklableSingleton()
    original.value = 999  # Modify state

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    # State should be preserved (same object)
    assert restored.value == 999


def test_singleton_pickle_different_classes_isolated():
    """Verify different singleton classes remain isolated after unpickling."""
    singleton1 = PicklableSingleton()
    singleton2 = AnotherPicklableSingleton()

    data1 = pickle.dumps(singleton1)
    data2 = pickle.dumps(singleton2)

    restored1 = pickle.loads(data1)
    restored2 = pickle.loads(data2)

    # Each should restore to its own singleton
    assert restored1 is singleton1
    assert restored2 is singleton2
    assert restored1 is not restored2


def test_singleton_pickle_counter_behavior():
    """Verify singleton counter increments on unpickle.

    Note: The counter increments because pickle calls __new__ during unpickle.
    Even though the same instance is returned, __new__ is invoked and
    increments the counter. This documents the actual behavior.
    """
    original = PicklableSingleton()
    count_after_create = SingletonMixin._counters[PicklableSingleton]

    data = pickle.dumps(original)
    pickle.loads(data)

    # Counter increments because __new__ is called during unpickle
    count_after_unpickle = SingletonMixin._counters[PicklableSingleton]
    assert count_after_unpickle == count_after_create + 1


def test_multiple_pickle_cycles_preserve_singleton():
    """Verify multiple pickle/unpickle cycles preserve singleton identity."""
    original = PicklableSingleton()

    # First cycle
    data1 = pickle.dumps(original)
    restored1 = pickle.loads(data1)

    # Second cycle
    data2 = pickle.dumps(restored1)
    restored2 = pickle.loads(data2)

    # All should be the same instance
    assert original is restored1 is restored2
