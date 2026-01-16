"""Immutable mixin supporting parameter-based identity and hashing.

This module provides ImmutableParameterizableMixin, which combines parameter
management with immutability to enable parameter-based object identity. This
allows parameterizable objects to be used as dictionary keys and set members,
with equality and hashing determined by their configuration parameters rather
than Python's id() function.
"""
from __future__ import annotations

from functools import cached_property
from typing import Any

from .parameterizable_mixin import ParameterizableMixin
from .immutable_mixin import ImmutableMixin
from ..utility_functions.json_processor import JsonSerializedObject


class ImmutableParameterizableMixin(ParameterizableMixin, ImmutableMixin):
    """Immutable objects with parameter-based identity and hashing.

    Combines ParameterizableMixin's parameter management with ImmutableMixin's
    immutability support. Objects use their JSON-serialized parameters as
    their identity key, enabling parameter-based equality comparisons and hashing.

    This design ensures that two instances with identical parameters are
    considered equal and have the same hash, regardless of when or where they
    were created. This makes it possible to use parameterizable objects as
    dictionary keys and set members.

    Note that the mixin does not enforce immutability; subclasses are
    responsible for ensuring their instances truly never change after
    initialization.
    """


    def get_identity_key(self) -> Any:
        """Return JSON-serialized parameters as identity key.

        Uses JSON-serialized parameters to ensure consistent, deterministic
        identity across instances. This approach guarantees that objects with
        identical parameters produce the same hash and compare as equal,
        enabling reliable use in hash-based collections.

        Returns:
            JSON string representation of parameters used for hashing
            and equality comparisons.
        """
        return self.jsparams

    @cached_property
    def jsparams(self) -> JsonSerializedObject:
        """Cached JSON-serialized parameters for identity operations.

        Provides a cached JSON representation of the object's parameters,
        used as the basis for hashing and equality comparisons. Caching
        ensures that serialization happens only once, improving performance
        for repeated identity operations.

        Returns:
            JSON string representation of the object's parameters.
        """
        return self.get_jsparams()
