"""Base mixin for immutable objects with identity-based hashing and equality."""
from __future__ import annotations

from functools import cached_property
from typing import Any, Self

from .guarded_init_metaclass import GuardedInitMeta


class ImmutableMixin(metaclass=GuardedInitMeta):
    """Provides immutability support with customizable identity keys.

    Objects are immutable after initialization and define their identity
    through a customizable identity_key() method. This enables safe use
    as dictionary keys and set members while preventing post-construction
    modification.

    Subclasses must override identity_key() to return a hashable value
    that uniquely identifies the object's identity.
    """

    def __init__(self, *args, **kwargs):
        self._init_finished = False
        super().__init__(*args, **kwargs)

    def identity_key(self) -> Any:
        """Return a hashable value defining this object's identity.

        This method must be overridden by subclasses to provide the value
        used for hashing and equality comparisons. The returned value must
        be hashable and should remain constant for the object's lifetime.

        Returns:
            A hashable value uniquely identifying this object.

        Raises:
            NotImplementedError: If not overridden by subclass.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement identity_key() method"
        )

    @cached_property
    def _cached_identity_key(self) -> Any:
        """Cache the identity key for consistent hashing.

        Returns:
            The cached identity key.

        Raises:
            RuntimeError: If called before initialization completes.
        """
        if not self._init_finished:
            raise RuntimeError("Cannot get identity key of uninitialized object")
        return self.identity_key()

    def __hash__(self) -> int:
        """Return hash based on cached identity key.

        Returns:
            Hash value derived from identity key.

        Raises:
            RuntimeError: If initialization is incomplete.
        """
        return hash(self._cached_identity_key)

    def __eq__(self, other: Any) -> bool:
        """Check equality based on type and identity key.

        Objects are equal if they share the same type and identity key value.
        Uses hash comparison first for optimization.

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
            return self._cached_identity_key == other._cached_identity_key

    def __ne__(self, other: Any) -> bool:
        """Check inequality based on type and identity key.

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
        """Return self since immutable objects need no copying."""
        return self

    def __deepcopy__(self, memo: dict) -> Self:
        """Return self since immutable objects need no deep copying."""
        return self
