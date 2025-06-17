"""Basic tests for parameterizable classes.

This module tests the fundamental functionality of parameterizable classes:
- Class recognition and registration
- Parameter serialization and deserialization
- Object reconstruction from portable parameters
"""

from src.parameterizable.parameterizable import *
from src.parameterizable.parameterizable import (
    _known_parameterizable_classes, _smoketest_parameterizable_class,
    _register_parameterizable_class)
from src.parameterizable.parameterizable import CLASSNAME_PARAM_KEY

from tests.demo_types import GoodPameterizable, EvenBetterOne, EmptyClass

import pytest

def test_good_class():
    """Test a properly implemented parameterizable class.

    This test verifies:
    1. The class is recognized as parameterizable
    2. The class passes the smoketest
    3. Registration works correctly
    4. Parameters can be serialized to a portable dictionary
    5. An object can be reconstructed from portable parameters
    """
    # Ensure the registry is clear
    _known_parameterizable_classes.clear()

    # Test class recognition and smoke-test
    assert is_parameterizable(GoodPameterizable)
    assert _smoketest_parameterizable_class(GoodPameterizable)

    # The smoke-test creates an instance which registers the class,
    # so we need to clear the registry again
    _known_parameterizable_classes.clear()

    # Test registration
    assert not is_registered(GoodPameterizable)
    _register_parameterizable_class(GoodPameterizable)
    assert is_registered(GoodPameterizable)
    assert len(_known_parameterizable_classes) == 1

    # Test parameter serialization
    obj = GoodPameterizable()
    obj.a = -12345
    obj.b = "Hi!"
    obj.c = str
    params = obj.__get_portable_params__()

    # Verify portable parameters structure
    assert CLASSNAME_PARAM_KEY in params
    assert params[CLASSNAME_PARAM_KEY] == "GoodPameterizable"
    assert params["a"] == -12345
    assert params["b"] == "Hi!"
    assert isinstance(params["c"], dict)
    assert BUILTIN_TYPE_KEY in params["c"]
    assert params["c"][BUILTIN_TYPE_KEY] == "__builtins__.str"

    # Test object reconstruction
    obj2 = get_object_from_portable_params(params)
    assert isinstance(obj2, GoodPameterizable)
    assert obj2.a == -12345
    assert obj2.b == "Hi!"
    assert obj2.c == str

def test_even_better_one():
    """Test a subclass of a parameterizable class.

    This test verifies:
    1. Subclasses are properly registered
    2. Parameter inheritance works correctly
    3. Objects can be serialized and reconstructed
    """
    # Ensure the registry is clear
    _known_parameterizable_classes.clear()

    # Test registration
    assert not is_registered(EvenBetterOne)
    obj = EvenBetterOne(a=20, b="subclass", c=float, d=6.28)
    assert is_registered(EvenBetterOne)

    # Test parameter inheritance
    params = obj.get_params()
    assert params["a"] == 20
    assert params["b"] == "subclass"
    assert params["c"] == float
    assert params["d"] == 6.28

    # Test serialization
    portable_params = obj.__get_portable_params__()
    assert portable_params[CLASSNAME_PARAM_KEY] == "EvenBetterOne"
    assert portable_params["a"] == 20
    assert portable_params["b"] == "subclass"
    assert portable_params["d"] == 6.28

    # Test reconstruction
    reconstructed = get_object_from_portable_params(portable_params)
    assert isinstance(reconstructed, EvenBetterOne)
    assert reconstructed.a == 20
    assert reconstructed.b == "subclass"
    assert reconstructed.c == float
    assert reconstructed.d == 6.28


def test_empty_class():
    """Test that non-parameterizable classes are correctly identified."""
    assert not is_parameterizable(EmptyClass)

    # Test that attempting to register a non-parameterizable class raises an error
    with pytest.raises(ValueError, match="is not parameterizable"):
        _register_parameterizable_class(EmptyClass)

    # Test with other non-parameterizable objects
    assert not is_parameterizable(None)
    assert not is_parameterizable(42)
    assert not is_parameterizable("string")
    assert not is_parameterizable([1, 2, 3])

    # Test with a class that has some but not all required methods
    class PartiallyParameterizable:
        def get_params(self):
            return {}

    assert not is_parameterizable(PartiallyParameterizable)
