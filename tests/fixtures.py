"""Test fixtures for parameterizable tests.

This module contains pytest fixtures that can be reused across test files
to reduce code duplication and improve test maintainability.
"""
from typing import Any

import pytest
from src.parameterizable.parameterizable import (
    ParameterizableClass
    , _known_parameterizable_classes
)

@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the registry of parameterizable classes before and after each test.
    
    This fixture is automatically used in all tests to ensure a clean state.
    """
    _known_parameterizable_classes.clear()
    yield
    _known_parameterizable_classes.clear()


@pytest.fixture
def basic_parameterizable_class():
    """Return a basic parameterizable class for testing."""
    class BasicParamClass(ParameterizableClass):
        def __init__(self, param1=10, param2="default", param3=int):
            super().__init__()
            self.param1 = param1
            self.param2 = param2
            self.param3 = param3
            
        def get_params(self) -> dict[str, Any]:
            return {
                "param1": self.param1,
                "param2": self.param2,
                "param3": self.param3
            }
    
    return BasicParamClass


@pytest.fixture
def nested_parameterizable_class(basic_parameterizable_class):
    """Return a parameterizable class that contains another parameterizable object."""
    class NestedParamClass(ParameterizableClass):
        def __init__(self, nested_obj=None, other_param="nested"):
            super().__init__()
            self.nested_obj = nested_obj if nested_obj else basic_parameterizable_class()
            self.other_param = other_param
            
        def get_params(self) -> dict[str, Any]:
            return {
                "nested_obj": self.nested_obj,
                "other_param": self.other_param
            }
    
    return NestedParamClass


@pytest.fixture
def collection_parameterizable_class(basic_parameterizable_class):
    """Return a parameterizable class that contains collections of objects."""
    class CollectionParamClass(ParameterizableClass):
        def __init__(self, obj_list=None, obj_dict=None):
            super().__init__()
            self.obj_list = obj_list if obj_list is not None else []
            self.obj_dict = obj_dict if obj_dict is not None else {}
            
        def get_params(self) -> dict[str, Any]:
            return {
                "obj_list": self.obj_list,
                "obj_dict": self.obj_dict
            }
    
    return CollectionParamClass