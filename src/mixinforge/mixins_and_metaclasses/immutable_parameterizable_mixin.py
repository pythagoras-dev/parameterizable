"""Immutable mixin supporting parameter-based identity and hashing."""
from __future__ import annotations

from functools import cache, cached_property
from typing import Self

from .parameterizable_mixin import ParameterizableMixin
from .guarded_init_metaclass import GuardedInitMeta
from ..utility_functions.json_processor import JsonSerializedObject

class ImmutableParameterizableMixin(ParameterizableMixin, metaclass=GuardedInitMeta):
    """Ensures single initialization and defines identity by parameter values.

    Objects are immutable after initialization and use parameters for equality
    comparisons and hashing. This enables safe use as dictionary keys and set
    members while preventing post-construction modification.
    """

    def __init__(self, *args, **kwargs):
        """Initialize immutability tracking and delegate to superclass.

        Args:
            *args: Positional arguments forwarded to superclass.
            **kwargs: Keyword arguments forwarded to superclass.
        """
        self._init_finished = False
        super().__init__(*args, **kwargs)


    @cached_property
    def _cached_jsparams(self) -> JsonSerializedObject:
        """Cache JSON-serialized parameters for consistent hashing."""
        return super().get_jsparams()

    def get_jsparams(self) -> JsonSerializedObject:
        """Return cached JSON-serialized parameters.

        Returns:
            JSON string representation of object parameters.
        """
        return self._cached_jsparams

    @cached_property
    def _cached_hash(self) -> int:
        """Compute and cache hash value based on parameters.

        Raises:
            RuntimeError: If called before initialization completes.
        """
        if not self._init_finished:
            raise RuntimeError("Cannot hash uninitialized object")
        return hash(self._cached_jsparams)

    def __hash__(self) -> int:
        """Return cached parameter-based hash.

        Returns:
            Hash value derived from JSON-serialized parameters.

        Raises:
            RuntimeError: If initialization is incomplete.
        """
        return self._cached_hash


    def __eq__(self, other: ImmutableParameterizableMixin) -> bool:
        """Check equality based on type and parameters.

        Objects are equal if they share the same type and parameter values.
        Uses hash comparison first for optimization.

        Args:
            other: Object to compare against.

        Returns:
            True if types and parameters match, False otherwise, or
            NotImplemented for incompatible types.
        """
        if self is other:
            return True
        elif type(self) is not type(other):
            return NotImplemented
        elif hash(self) != hash(other):
            return False
        else:
            return self._cached_jsparams == other._cached_jsparams

    def __copy__(self) -> Self:
        """Return self since immutable objects need no copying."""
        return self

    def __deepcopy__(self, memo: dict) -> Self:
        """Return self since immutable objects need no deep copying."""
        return self
