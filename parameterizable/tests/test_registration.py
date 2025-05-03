from parameterizable.parameterizable import *
from parameterizable.parameterizable import _known_parameterizable_classes
from parameterizable.parameterizable import _smoketest_known_parameterizable_classes
import pytest
from abc import *

# Import the test classes from test_basic to reuse them
from parameterizable.tests.test_basic import GoodPameterizable, EvenBetterOne, EmptyClass

def test_is_registered():
    _known_parameterizable_classes.clear()
    # Test that a class is not registered initially
    assert not is_registered(GoodPameterizable)

    # Test that a class is registered after instantiation
    obj = GoodPameterizable()
    assert is_registered(GoodPameterizable)

    _known_parameterizable_classes.clear()

    # Test direct registration
    register_parameterizable_class(GoodPameterizable)
    assert is_registered(GoodPameterizable)

    _known_parameterizable_classes.clear()


def test_register_parameterizable_class_errors():
    _known_parameterizable_classes.clear()

    # Test registering a non-parameterizable class
    with pytest.raises(ValueError):
        register_parameterizable_class(EmptyClass)

    # Create a class with the same name as GoodPameterizable but different identity
    class GoodPameterizable:
        pass

    # Register the original GoodPameterizable
    register_parameterizable_class(globals()["GoodPameterizable"])

    # Try to register the new class with the same name
    with pytest.raises(ValueError, match="is already registered with a different identity"):
        register_parameterizable_class(GoodPameterizable)

    _known_parameterizable_classes.clear()


def test_smoketest_known_parameterizable_classes():
    _known_parameterizable_classes.clear()

    # Register multiple parameterizable classes
    register_parameterizable_class(GoodPameterizable)
    register_parameterizable_class(EvenBetterOne)

    # Test that smoketest runs without errors
    _smoketest_known_parameterizable_classes()

    _known_parameterizable_classes.clear()