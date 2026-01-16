"""Immutable mixin supporting parameter-based identity and hashing."""
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

    This makes it possible to use parameterizable objects as dictionary keys
    and set members.
    """


    def get_identity_key(self) -> Any:
        """Return JSON-serialized parameters as identity key.

        Returns:
            JSON string representation of parameters used for hashing
            and equality comparisons.
        """
        return self.jsparams

    @cached_property
    def jsparams(self) -> JsonSerializedObject:
        """Cached JSON-serialized parameters.

        Returns:
            Cached JSON string of parameters.
        """
        return self.get_jsparams()
