""" This module tests complex object hierarchies
"""

import pytest
from src.parameterizable.parameterizable import (
    ParameterizableClass,
    get_object_from_portable_params,
    _known_parameterizable_classes
)
from tests.fixtures import (
    basic_parameterizable_class,
    nested_parameterizable_class
)



def test_complex_object_hierarchy(basic_parameterizable_class):
    """Test a complex object hierarchy with multiple nested objects."""

    # Clear the registry before the test
    _known_parameterizable_classes.clear()

    # Create a class that contains multiple parameterizable objects
    class ComplexHierarchyClass(ParameterizableClass):
        def __init__(self, obj1=None, obj2=None, obj3=None):
            super().__init__()
            self.obj1 = obj1 if obj1 else basic_parameterizable_class(param1=1)
            self.obj2 = obj2 if obj2 else basic_parameterizable_class(param1=2)
            self.obj3 = obj3 if obj3 else basic_parameterizable_class(param1=3)

        def get_params(self):
            return {
                "obj1": self.obj1,
                "obj2": self.obj2,
                "obj3": self.obj3
            }

    # Create an object with multiple nested objects
    obj = ComplexHierarchyClass()

    # Convert to portable params
    portable_params = obj.get_portable_params()

    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)

    # Verify the reconstructed object
    assert reconstructed.obj1.param1 == 1
    assert reconstructed.obj2.param1 == 2
    assert reconstructed.obj3.param1 == 3
