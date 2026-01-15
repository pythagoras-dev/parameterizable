"""Tests for ImmutableMixin."""
import pytest
from mixinforge.mixins_and_metaclasses.immutable_mixin import ImmutableMixin


class StringIdentifiable(ImmutableMixin):
    """Concrete implementation using a string as identity key."""
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def get_identity_key(self):
        return self.name


class TupleIdentifiable(ImmutableMixin):
    """Concrete implementation using a tuple as identity key."""
    def __init__(self, x: int, y: int):
        super().__init__()
        self.x = x
        self.y = y

    def get_identity_key(self):
        return (self.x, self.y)


class SubclassOfStringIdentifiable(StringIdentifiable):
    """Subclass to test type inequality."""
    pass


def test_abstract_identity_key():
    """Verify identity_key() must be overridden."""
    class NoIdentityKey(ImmutableMixin):
        def __init__(self):
            super().__init__()

    obj = NoIdentityKey()
    with pytest.raises(NotImplementedError, match="must implement identity_key"):
        obj.get_identity_key()


def test_equality_with_same_identity():
    """Verify objects with identical identity keys are equal."""
    s1 = StringIdentifiable("alice")
    s2 = StringIdentifiable("alice")

    assert s1 == s2
    assert s2 == s1


def test_inequality_with_different_identity():
    """Verify objects with different identity keys are not equal."""
    s1 = StringIdentifiable("alice")
    s2 = StringIdentifiable("bob")

    assert s1 != s2


def test_inequality_with_different_types():
    """Verify objects of different types are not equal even with same identity."""
    s1 = StringIdentifiable("alice")
    s2 = SubclassOfStringIdentifiable("alice")

    # Even though identity keys are same, types are different
    assert s1 != s2
    assert s2 != s1


def test_equality_with_other_types():
    """Verify inequality with completely different types."""
    s = StringIdentifiable("alice")
    assert s != None
    assert s != "alice"
    assert s != 123
    assert s != object()


def test_hashing_consistency():
    """Verify hash is consistent with equality."""
    s1 = StringIdentifiable("alice")
    s2 = StringIdentifiable("alice")
    s3 = StringIdentifiable("bob")

    assert hash(s1) == hash(s2)
    assert hash(s1) != hash(s3)

    # Verify hash stability
    assert hash(s1) == hash(s1)


def test_hashing_with_tuple_identity():
    """Verify hashing works with tuple identity keys."""
    t1 = TupleIdentifiable(1, 2)
    t2 = TupleIdentifiable(1, 2)
    t3 = TupleIdentifiable(3, 4)

    assert hash(t1) == hash(t2)
    assert hash(t1) != hash(t3)


def test_hash_fails_during_initialization():
    """Verify hashing raises RuntimeError if called before init finishes."""
    class PrematureHasher(ImmutableMixin):
        def __init__(self):
            super().__init__()
            # Accessing hash before init is done
            hash(self)

        def get_identity_key(self):
            return "test"

    with pytest.raises(RuntimeError, match="Cannot get identity key of uninitialized object"):
        PrematureHasher()


def test_initialization_guard_compliance():
    """Verify that failing to set _init_finished=False triggers GuardedInitMeta error."""
    # If we DON'T call super().__init__(), _init_finished might not be set to False
    # GuardedInitMeta requires _init_finished to be False at the end of __init__

    class BadInit(ImmutableMixin):
        def __init__(self):
            # Deliberately skip super().__init__() which sets _init_finished = False
            pass

        def get_identity_key(self):
            return "test"

    with pytest.raises(RuntimeError, match="must set attribute _init_finished to False"):
        BadInit()


def test_copy_returns_self():
    """Verify __copy__ returns the same object."""
    import copy

    s = StringIdentifiable("alice")
    s_copy = copy.copy(s)

    assert s_copy is s


def test_deepcopy_returns_self():
    """Verify __deepcopy__ returns the same object."""
    import copy

    s = StringIdentifiable("alice")
    s_deepcopy = copy.deepcopy(s)

    assert s_deepcopy is s


def test_identity_same_object():
    """Verify object equals itself."""
    s = StringIdentifiable("alice")
    assert s == s


def test_use_as_dict_key():
    """Verify immutable objects can be used as dictionary keys."""
    s1 = StringIdentifiable("alice")
    s2 = StringIdentifiable("bob")
    s3 = StringIdentifiable("alice")  # Same identity as s1

    d = {s1: "first", s2: "second"}

    assert d[s1] == "first"
    assert d[s2] == "second"
    assert d[s3] == "first"  # Should retrieve same value as s1


def test_use_in_set():
    """Verify immutable objects can be used in sets."""
    s1 = StringIdentifiable("alice")
    s2 = StringIdentifiable("bob")
    s3 = StringIdentifiable("alice")  # Duplicate of s1

    my_set = {s1, s2, s3}

    # Set should only contain 2 unique items (s3 is duplicate of s1)
    assert len(my_set) == 2
    assert s1 in my_set
    assert s2 in my_set
    assert s3 in my_set


def test_cached_identity_key():
    """Verify identity key is cached after first access."""
    call_count = 0

    class CountingIdentifiable(ImmutableMixin):
        def __init__(self, value):
            super().__init__()
            self.value = value

        def get_identity_key(self):
            nonlocal call_count
            call_count += 1
            return self.value

    obj = CountingIdentifiable("test")

    # First hash should call identity_key()
    hash(obj)
    assert call_count == 1

    # Second hash should use cached value
    hash(obj)
    assert call_count == 1  # Still 1, not incremented

    # Equality check should also use cached value
    obj2 = CountingIdentifiable("test")
    obj == obj2
    # call_count should now be 2 (one for obj, one for obj2)
    assert call_count == 2
