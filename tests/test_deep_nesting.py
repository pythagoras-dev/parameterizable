"""Tests for deep nesting of parameterizable objects.

This module tests:
- Deep nesting (objects within objects within objects)
- Potential circular references
- Complex object hierarchies
"""

import pytest
from parameterizable import (
    ParameterizableClass,
    get_object_from_portable_params,
    CLASSNAME_PARAM_KEY
)
from parameterizable import (
    clear_registry,
    basic_parameterizable_class,
    nested_parameterizable_class
)


def test_deep_nesting(basic_parameterizable_class, nested_parameterizable_class):
    """Test deep nesting of parameterizable objects (3+ levels deep)."""
    # Create a deeply nested structure:
    # DeepNestingClass -> NestedParamClass -> BasicParamClass
    
    class DeepNestingClass(ParameterizableClass):
        def __init__(self, nested_obj=None, top_level_param="top"):
            super().__init__()
            self.nested_obj = nested_obj if nested_obj else nested_parameterizable_class()
            self.top_level_param = top_level_param
            
        def get_params(self):
            return {
                "nested_obj": self.nested_obj,
                "top_level_param": self.top_level_param
            }
    
    # Create basic object
    basic_obj = basic_parameterizable_class(param1=100, param2="level3", param3=str)
    
    # Create middle level object that contains the basic object
    middle_obj = nested_parameterizable_class(nested_obj=basic_obj, other_param="level2")
    
    # Create top level object that contains the middle object
    top_obj = DeepNestingClass(nested_obj=middle_obj, top_level_param="level1")
    
    # Convert to portable params
    portable_params = top_obj.__get_portable_params__()
    
    # Verify the structure of the portable params
    assert CLASSNAME_PARAM_KEY in portable_params
    assert portable_params[CLASSNAME_PARAM_KEY] == "DeepNestingClass"
    assert portable_params["top_level_param"] == "level1"
    
    assert CLASSNAME_PARAM_KEY in portable_params["nested_obj"]
    assert portable_params["nested_obj"][CLASSNAME_PARAM_KEY] == "NestedParamClass"
    assert portable_params["nested_obj"]["other_param"] == "level2"
    
    assert CLASSNAME_PARAM_KEY in portable_params["nested_obj"]["nested_obj"]
    assert portable_params["nested_obj"]["nested_obj"][CLASSNAME_PARAM_KEY] == "BasicParamClass"
    assert portable_params["nested_obj"]["nested_obj"]["param1"] == 100
    assert portable_params["nested_obj"]["nested_obj"]["param2"] == "level3"
    
    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)
    
    # Verify the reconstructed object
    assert reconstructed.top_level_param == "level1"
    assert reconstructed.nested_obj.other_param == "level2"
    assert reconstructed.nested_obj.nested_obj.param1 == 100
    assert reconstructed.nested_obj.nested_obj.param2 == "level3"
    assert reconstructed.nested_obj.nested_obj.param3 == str


def test_complex_object_hierarchy(basic_parameterizable_class):
    """Test a complex object hierarchy with multiple nested objects."""
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
    portable_params = obj.__get_portable_params__()
    
    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)
    
    # Verify the reconstructed object
    assert reconstructed.obj1.param1 == 1
    assert reconstructed.obj2.param1 == 2
    assert reconstructed.obj3.param1 == 3


def test_circular_reference_detection():
    """Test that circular references are detected and handled appropriately."""
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