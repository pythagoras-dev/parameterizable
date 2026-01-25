"""Integration tests for mixin composition.

The library encourages composing mixins, but there are potential risks:
- Metaclass conflicts
- Initialization order issues
- Method resolution order (MRO) conflicts

These tests verify that common mixin combinations work correctly together.
"""
import pickle
from typing import Any

from mixinforge import (
    SingletonMixin,
    ImmutableMixin,
    ParameterizableMixin,
)


# =============================================================================
# Test Classes: SingletonMixin + ImmutableMixin
# =============================================================================


class SingletonImmutable(SingletonMixin, ImmutableMixin):
    """Class combining SingletonMixin and ImmutableMixin.

    This is a common pattern: a singleton that is also immutable and hashable.
    """

    def __init__(self, name: str = "default"):
        super().__init__()
        self.name = name

    def get_identity_key(self):
        return self.name

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("_init_finished", None)
        return state


# =============================================================================
# Test Classes: ParameterizableMixin + ImmutableMixin
# =============================================================================


class ParameterizableImmutable(ParameterizableMixin, ImmutableMixin):
    """Class combining ParameterizableMixin and ImmutableMixin.

    Useful for configuration objects that should be hashable and JSON-serializable.
    """

    def __init__(self, x: int, y: int = 10):
        super().__init__()
        self.x = x
        self.y = y

    def get_identity_key(self):
        return (self.x, self.y)

    def get_params(self) -> dict[str, Any]:
        return {"x": self.x, "y": self.y}

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("_init_finished", None)
        return state


# =============================================================================
# Test Classes: All Three Mixins
# =============================================================================


class TripleMixin(SingletonMixin, ParameterizableMixin, ImmutableMixin):
    """Class combining all three major mixins.

    Note: SingletonMixin inherits from ParameterizableMixin, so this tests
    the MRO resolution when ParameterizableMixin appears multiple times.
    """

    def __init__(self, config_name: str = "default"):
        super().__init__()
        self.config_name = config_name

    def get_identity_key(self):
        return self.config_name

    def get_params(self) -> dict[str, Any]:
        return {"config_name": self.config_name}

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("_init_finished", None)
        return state


# =============================================================================
# Tests: SingletonMixin + ImmutableMixin
# =============================================================================


def test_singleton_immutable_returns_same_instance():
    """Verify SingletonMixin behavior works with ImmutableMixin."""
    s1 = SingletonImmutable("test")
    s2 = SingletonImmutable("ignored")  # Args ignored after first instantiation

    assert s1 is s2


def test_singleton_immutable_is_hashable():
    """Verify ImmutableMixin __hash__ works with SingletonMixin."""
    obj = SingletonImmutable("test")

    assert obj._init_finished is True
    h = hash(obj)
    assert h == hash(obj)  # Consistent hash


def test_singleton_immutable_in_set():
    """Verify combined mixin works in sets."""
    obj1 = SingletonImmutable("test")
    obj2 = SingletonImmutable("test")  # Same singleton

    s = {obj1, obj2}
    assert len(s) == 1  # Same object, so only 1 in set


def test_singleton_immutable_as_dict_key():
    """Verify combined mixin works as dictionary key."""
    obj = SingletonImmutable("test")
    d = {obj: "value"}

    # Same singleton should retrieve the value
    obj2 = SingletonImmutable("test")
    assert d[obj2] == "value"


def test_singleton_immutable_equality():
    """Verify equality works correctly."""
    obj1 = SingletonImmutable("test")
    obj2 = SingletonImmutable("test")

    # Same singleton instance
    assert obj1 == obj2
    assert obj1 is obj2


def test_singleton_immutable_pickle():
    """Verify pickling works with combined mixins."""
    original = SingletonImmutable("test")

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    # Singleton: should be same instance
    assert restored is original
    # Immutable: should be hashable
    assert hash(restored) == hash(original)
    assert restored._init_finished is True


# =============================================================================
# Tests: ParameterizableMixin + ImmutableMixin
# =============================================================================


def test_parameterizable_immutable_params():
    """Verify ParameterizableMixin methods work with ImmutableMixin."""
    obj = ParameterizableImmutable(x=5, y=15)

    params = obj.get_params()
    assert params == {"x": 5, "y": 15}

    jsparams = obj.get_jsparams()
    assert '"x": 5' in jsparams
    assert '"y": 15' in jsparams


def test_parameterizable_immutable_hashable():
    """Verify ImmutableMixin hash works with ParameterizableMixin."""
    obj1 = ParameterizableImmutable(x=5, y=15)
    obj2 = ParameterizableImmutable(x=5, y=15)

    assert hash(obj1) == hash(obj2)
    assert obj1 == obj2


def test_parameterizable_immutable_in_set():
    """Verify ParameterizableImmutable works in sets."""
    obj1 = ParameterizableImmutable(x=1, y=2)
    obj2 = ParameterizableImmutable(x=1, y=2)
    obj3 = ParameterizableImmutable(x=3, y=4)

    s = {obj1, obj2, obj3}
    assert len(s) == 2  # obj1 and obj2 are equal


def test_parameterizable_immutable_pickle():
    """Verify pickling works with ParameterizableMixin + ImmutableMixin."""
    original = ParameterizableImmutable(x=10, y=20)

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    assert restored.get_params() == original.get_params()
    assert hash(restored) == hash(original)
    assert restored == original
    assert restored._init_finished is True


def test_parameterizable_immutable_default_params():
    """Verify class-level default params work correctly."""
    defaults = ParameterizableImmutable.get_default_params()
    assert defaults == {"y": 10}  # Only y has default


# =============================================================================
# Tests: Triple Mixin Composition
# =============================================================================


def test_triple_mixin_singleton():
    """Verify singleton behavior in triple mixin."""
    obj1 = TripleMixin("config")
    obj2 = TripleMixin("ignored")

    assert obj1 is obj2


def test_triple_mixin_hashable():
    """Verify hash works in triple mixin."""
    obj = TripleMixin("config")

    h = hash(obj)
    assert h == hash(obj)


def test_triple_mixin_parameterizable():
    """Verify get_params works in triple mixin."""
    obj = TripleMixin("config")

    params = obj.get_params()
    assert params == {"config_name": "config"}


def test_triple_mixin_pickle():
    """Verify pickling works with triple mixin."""
    original = TripleMixin("config")

    data = pickle.dumps(original)
    restored = pickle.loads(data)

    assert restored is original  # Singleton preserved
    assert hash(restored) == hash(original)  # Immutable preserved
    assert restored.get_params() == original.get_params()  # Parameterizable preserved


def test_triple_mixin_init_finished():
    """Verify _init_finished is set correctly."""
    obj = TripleMixin("config")
    assert obj._init_finished is True


def test_triple_mixin_repr():
    """Verify repr works correctly."""
    obj = TripleMixin("config")
    r = repr(obj)

    assert "TripleMixin" in r
    assert "config_name" in r


# =============================================================================
# Tests: MRO and Inheritance
# =============================================================================


def test_singleton_immutable_mro():
    """Verify MRO is sensible for SingletonImmutable."""
    mro = SingletonImmutable.__mro__

    # SingletonMixin should come before ImmutableMixin
    singleton_idx = mro.index(SingletonMixin)
    immutable_idx = mro.index(ImmutableMixin)
    assert singleton_idx < immutable_idx


def test_parameterizable_immutable_mro():
    """Verify MRO is sensible for ParameterizableImmutable."""
    mro = ParameterizableImmutable.__mro__

    # ParameterizableMixin should come before ImmutableMixin
    param_idx = mro.index(ParameterizableMixin)
    immutable_idx = mro.index(ImmutableMixin)
    assert param_idx < immutable_idx


def test_triple_mixin_mro_no_conflicts():
    """Verify triple mixin MRO resolves without conflicts."""
    # This should not raise TypeError about MRO conflicts
    mro = TripleMixin.__mro__

    # All mixins should be in MRO
    assert SingletonMixin in mro
    assert ParameterizableMixin in mro
    assert ImmutableMixin in mro


# =============================================================================
# Tests: Edge Cases
# =============================================================================


def test_singleton_immutable_identity_key_stability():
    """Verify identity_key is stable across singleton accesses."""
    obj1 = SingletonImmutable("stable")
    key1 = obj1.identity_key

    obj2 = SingletonImmutable("stable")
    key2 = obj2.identity_key

    assert key1 == key2
    assert obj1 is obj2


def test_different_singleton_immutables_have_different_hashes():
    """Verify different singleton classes have different instances."""

    class SingletonImmutableA(SingletonMixin, ImmutableMixin):
        def __init__(self):
            super().__init__()
            self.name = "A"

        def get_identity_key(self):
            return self.name

    class SingletonImmutableB(SingletonMixin, ImmutableMixin):
        def __init__(self):
            super().__init__()
            self.name = "B"

        def get_identity_key(self):
            return self.name

    a = SingletonImmutableA()
    b = SingletonImmutableB()

    assert a is not b
    assert a != b  # Different identity keys
    assert hash(a) != hash(b)
