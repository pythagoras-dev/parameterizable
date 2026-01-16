"""Mixin for immutable objects with optimized hashing and equality.

Provides the ImmutableMixin class that enables value-based identity,
cached hashing, and optimized equality comparisons for objects that never
change after initialization. Subclasses define their identity through a
customizable key rather than through Python's id() function.
"""
from __future__ import annotations

from functools import cached_property
from typing import Any, Self

from .guarded_init_metaclass import GuardedInitMeta


class ImmutableMixin(metaclass=GuardedInitMeta):
    """Base mixin for objects that never change after initialization.

    Provides value-based identity semantics with optimized hashing and
    equality comparisons. Instead of using object identity (id), instances
    are compared based on a customizable identity key that represents their
    immutable state. This enables efficient use in sets and dictionaries
    while supporting value equality semantics.

    The mixin caches the hash value for O(1) lookups and uses hash-based
    short-circuiting in equality checks to avoid expensive comparisons.
    This is particularly beneficial for complex objects with many fields.

    Note that this mixin does not enforce immutability; subclasses are
    responsible for ensuring their instances truly never change after
    initialization.

    Subclasses must override get_identity_key() to return a hashable value
    that uniquely defines the object's identity based on its immutable state.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the mixin with an initialization guard.

        Sets up the _init_finished flag to prevent premature access to the
        identity key during object construction. The GuardedInitMeta
        metaclass sets this flag to True after initialization completes.
        """
        self._init_finished = False
        super().__init__(*args, **kwargs)

    def get_identity_key(self) -> Any:
        """Return a hashable value defining this object's identity.

        Subclasses must override this method to specify what makes an
        instance unique. The returned value is used for hashing and equality
        comparisons, enabling value-based semantics. Common implementations
        return a tuple of the object's immutable fields.

        The returned value must be hashable and must remain constant for
        the object's lifetime to maintain hash consistency.

        Returns:
            A hashable value uniquely identifying this object based on its
            immutable state.

        Raises:
            NotImplementedError: If not overridden by subclass.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement identity_key() method"
        )

    @cached_property
    def identity_key(self) -> Any:
        """Cached identity key for consistent hashing and equality checks.

        Caches the result of get_identity_key() to ensure the same value
        is used throughout the object's lifetime. This guarantees hash
        stability and enables efficient repeated comparisons without
        recomputing the identity key.

        Returns:
            The cached identity key.

        Raises:
            RuntimeError: If called before initialization completes.
        """
        if not self._init_finished:
            raise RuntimeError("Cannot get identity key of uninitialized object")
        return self.get_identity_key()

    def __hash__(self) -> int:
        """Return hash based on the cached identity key.

        Uses the cached identity key to compute the hash, ensuring O(1)
        performance for repeated hash operations. This enables efficient
        use in sets and dictionaries.

        Returns:
            Hash value derived from the identity key.

        Raises:
            RuntimeError: If initialization is incomplete.
        """
        return hash(self.identity_key)

    def __eq__(self, other: Any) -> bool:
        """Check equality based on type and identity key.

        Implements optimized equality checking with multiple short-circuit
        paths: identity check, type check, hash comparison, and finally
        identity key comparison. The hash comparison provides fast rejection
        for unequal objects without comparing full identity keys.

        Args:
            other: Object to compare against.

        Returns:
            True if types and identity keys match, False otherwise, or
            NotImplemented for incompatible types.
        """
        if self is other:
            return True
        elif type(self) is not type(other):
            return NotImplemented
        elif hash(self) != hash(other):
            return False
        else:
            return self.identity_key == other.identity_key

    def __ne__(self, other: Any) -> bool:
        """Check inequality based on type and identity key.

        Delegates to __eq__ and inverts the result, maintaining consistency
        with equality semantics and properly handling NotImplemented.

        Args:
            other: Object to compare against.

        Returns:
            True if objects are not equal, False otherwise, or
            NotImplemented for incompatible types.
        """
        eq_result = self.__eq__(other)
        if eq_result is NotImplemented:
            return NotImplemented
        return not eq_result

    def __copy__(self) -> Self:
        """Return self since immutable objects need no copying.
        
        Immutable objects can safely share references instead of creating
        copies, improving memory efficiency and performance.
        """
        return self

    def __deepcopy__(self, memo: dict) -> Self:
        """Return self since immutable objects need no deep copying.
        
        Immutable objects can safely share references instead of creating
        deep copies, improving memory efficiency and performance.
        """
        return self
