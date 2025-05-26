"""Basic tests for parameterizable classes.

This module offers sample classes that are used
for testing the fundamental
"""

from src.parameterizable.parameterizable import *

from abc import ABC

class GoodPameterizable(ABC, ParameterizableClass):
    """A well-implemented parameterizable class for testing."""
    def __init__(self, a: int = 10, b: str = "hello", c=int):
        ParameterizableClass.__init__(self)
        self.a = a
        self.b = b
        self.c = c

    def get_params(self) -> dict[str, Any]:
        """Get the parameters of the object."""
        params = dict(a=self.a, b=self.b, c=self.c)
        return params


class EvenBetterOne(GoodPameterizable):
    """A subclass of GoodPameterizable that adds another parameter."""
    def __init__(self, a: int = 10, b: str = "hello", c=int, d: float = 3.14):
        GoodPameterizable.__init__(self, a, b, c)
        self.d = d

    def get_params(self) -> dict[str, Any]:
        """Get the parameters of the object, including inherited ones."""
        params = super().get_params()
        params["d"] = self.d
        return params


class EmptyClass:
    """A class that doesn't implement the parameterizable interface."""
    pass

