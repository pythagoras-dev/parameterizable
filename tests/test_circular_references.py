""" This module tests Potential circular references
"""

import pytest
from src.parameterizable.parameterizable import (
    ParameterizableClass,
    _known_parameterizable_classes)



def test_circular_reference_detection():
    """Test that circular references are detected and handled appropriately."""

    # Clear the registry before the test
    _known_parameterizable_classes.clear()

    # Create a class that could potentially have a circular reference
    class CircularClass(ParameterizableClass):
        def __init__(self, name="circular", ref=None):
            super().__init__()
            self.name = name
            self.ref = ref

        def get_params(self):
            return {
                "name": self.name,
                "ref": self.ref
            }

    # Create an object with a circular reference
    obj1 = CircularClass(name="obj1")
    obj2 = CircularClass(name="obj2", ref=obj1)
    obj1.ref = obj2  # Create circular reference: obj1 -> obj2 -> obj1

    # Attempting to convert to portable params should raise an error
    # due to infinite recursion
    with pytest.raises(RecursionError):
        portable_params = obj1.__get_portable_params__()