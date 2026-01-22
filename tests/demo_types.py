"""Basic tests for mixinforge classes.

This module offers sample classes that are used
for testing the fundamental
"""

from abc import ABC
from typing import Any

from mixinforge.mixins_and_metaclasses.parameterizable_mixin import ParameterizableMixin

class GoodParameterizable(ABC, ParameterizableMixin):
    """A well-implemented mixinforge class for testing."""
    def __init__(self, a: int = 10, b: str = "hello", c:type=int):
        ParameterizableMixin.__init__(self)
        self.a = a
        self.b = b
        self.c = c

    def get_params(self) -> dict[str, Any]:
        """Get the parameters of the object."""
        params = dict(a=self.a, b=self.b, c=self.c)
        return params


class EvenBetterOne(GoodParameterizable):
    """A subclass of GoodParameterizable that adds another parameter."""
    def __init__(self, a: int = 10, b: str = "hello", c=int, d: float = 3.14):
        GoodParameterizable.__init__(self, a, b, c)
        self.d = d

    def get_params(self) -> dict[str, Any]:
        """Get the parameters of the object, including inherited ones."""
        params = super().get_params()
        params["d"] = self.d
        return params


class EmptyClass:
    """A class that doesn't implement the mixinforge interface."""
    pass
