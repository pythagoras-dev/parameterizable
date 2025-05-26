"""This module tests Deep nesting (objects within objects within objects)
"""

import pytest
from src.parameterizable.parameterizable import (
    ParameterizableClass,
    get_object_from_portable_params,
    CLASSNAME_PARAM_KEY,
    _known_parameterizable_classes
)
from tests.fixtures import (
    basic_parameterizable_class,
    nested_parameterizable_class
)


def test_deep_nesting(basic_parameterizable_class, nested_parameterizable_class):
    """Test deep nesting of parameterizable objects (3+ levels deep)."""
    # Create a deeply nested structure:
    # DeepNestingClass -> NestedParamClass -> BasicParamClass

    _known_parameterizable_classes.clear()

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