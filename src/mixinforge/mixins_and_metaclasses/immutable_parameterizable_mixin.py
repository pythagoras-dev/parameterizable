"""Mixin for creating immutable parameterizable objects."""
from __future__ import annotations

from .parameterizable_mixin import ParameterizableMixin
from .guarded_init_metaclass import GuardedInitMeta

class ImmutableParameterizableMixin(ParameterizableMixin, metaclass=GuardedInitMeta):
    """Enforces immutability and params-based identity.

    Ensures objects are initialized strictly once and defines equality/hashing
    based on parameter values.
    """

    def __init__(self, *args, **kwargs):
        """Sets the initialization guard and delegates to superclass.

        Args:
            *args: Passed to superclass.
            **kwargs: Passed to superclass.
        """
        self._init_finished = False
        super().__init__(*args, **kwargs)

    def __hash__(self) -> int:
        """Computes hash based on parameters.

        Returns:
            Hash of the JSON-serialized parameters.

        Raises:
            RuntimeError: If initialization is incomplete.
        """
        if not self._init_finished:
            raise RuntimeError("Cannot hash uninitialized object")
        return hash(self.get_jsparams())

    def __eq__(self, other: ImmutableParameterizableMixin) -> bool:
        """Checks params-based equality.

        Objects are equal if they have the exact same type and identical parameters.

        Args:
            other: Object to compare.

        Returns:
            True if equal, False otherwise.
        """
        if type(self) != type(other):
            return False
        return self.get_jsparams() == other.get_jsparams()
