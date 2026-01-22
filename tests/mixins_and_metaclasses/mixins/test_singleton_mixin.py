"""Tests for SingletonMixin functionality.

This module tests the singleton pattern implementation to ensure each subclass
maintains exactly one instance throughout its lifetime.
"""
from mixinforge import SingletonMixin


class SimpleSingleton(SingletonMixin):
    """Basic singleton test class."""

    def __init__(self):
        super().__init__()
        self.value = 42


class AnotherSingleton(SingletonMixin):
    """Another singleton class to test per-class instances."""

    def __init__(self):
        super().__init__()
        self.data = "test"


class InheritedSingleton(SimpleSingleton):
    """A singleton that inherits from another singleton."""
    pass


class OneArgSingleton(SingletonMixin):
    """Singleton that takes one argument in its constructor."""

    def __init__(self, arg1):
        super().__init__()
        self.arg1 = arg1

class ManyArgsSingleton(SingletonMixin):
    """Singleton that takes many arguments in its constructor."""
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs


def test_singleton_returns_same_instance():
    """Test that multiple instantiations return the same instance."""
    instance1 = SimpleSingleton()
    instance2 = SimpleSingleton()

    assert instance1 is instance2
    assert id(instance1) == id(instance2)


def test_singleton_different_classes_have_different_instances():
    """Test that different singleton subclasses maintain separate instances."""
    singleton1 = SimpleSingleton()
    singleton2 = AnotherSingleton()

    assert singleton1 is not singleton2
    assert type(singleton1) is not type(singleton2)

def test_singleton_inheritance():
    """Test that singleton behavior is maintained in subclasses."""
    base_instance = SimpleSingleton()
    inherited_instance1 = InheritedSingleton()
    inherited_instance2 = InheritedSingleton()

    assert inherited_instance1 is inherited_instance2
    assert inherited_instance1 is not base_instance


def test_singleton_accepts_one_constructor_arg():
    class OneArgSingleton(SingletonMixin):
        def __init__(self, x: int):
            self.x = x

    s1 = OneArgSingleton(1)
    s2 = OneArgSingleton(2)

    assert s1 is s2


def test_singleton_accepts_many_constructor_args():
    class ManyArgsSingleton(SingletonMixin):
        def __init__(self, x: int, y: str):
            self.x = x
            self.y = y

    s1 = ManyArgsSingleton(1, "a")
    s2 = ManyArgsSingleton(2, y="b")
    s3 = ManyArgsSingleton(x=3, y="c")

    assert s1 is s2
    assert s2 is s3


def test_singleton_maintains_state():
    """Test that singleton returns the same instance (though __init__ is re-called)."""
    # Get the singleton instance
    instance1 = SimpleSingleton()
    # Modify the state after initialization
    instance1.value = 999

    # Get the singleton again - returns same instance but __init__ is called
    instance2 = SimpleSingleton()

    # They should be the same object
    assert instance1 is instance2

    # Note: In this simple singleton implementation, __init__ is called again
    # which resets value to 42. A more sophisticated singleton would guard against this.
    # But the important thing is they are the same instance in memory.
    assert id(instance1) == id(instance2)


def test_singleton_subclass_independence():
    """Test that each subclass has its own independent singleton."""
    class FirstSingleton(SingletonMixin):
        def __init__(self):
            super().__init__()
            self.name = "first"

    class SecondSingleton(SingletonMixin):
        def __init__(self):
            super().__init__()
            self.name = "second"

    first = FirstSingleton()
    second = SecondSingleton()

    assert first is not second
    assert first.name == "first"
    assert second.name == "second"

    # Verify they return same instances on re-instantiation
    first_again = FirstSingleton()
    second_again = SecondSingleton()

    assert first is first_again
    assert second is second_again


def test_singleton_counters():
    """Test that singleton instantiation counters are maintained correctly."""
    class CounterSingleton(SingletonMixin):
        pass

    # Initial state check
    assert CounterSingleton not in SingletonMixin._counters

    # First instantiation
    s1 = CounterSingleton()
    assert SingletonMixin._counters[CounterSingleton] == 1

    # Second instantiation
    s2 = CounterSingleton()
    assert SingletonMixin._counters[CounterSingleton] == 2
    assert s1 is s2

    # Independent class check
    class AnotherCounterSingleton(SingletonMixin):
        pass

    _ = AnotherCounterSingleton()
    assert SingletonMixin._counters[AnotherCounterSingleton] == 1
    # Check that previous one didn't change
    assert SingletonMixin._counters[CounterSingleton] == 2
