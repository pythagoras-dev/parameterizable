from src.parameterizable.parameterizable import *
from src.parameterizable.parameterizable import _known_parameterizable_classes
from src.parameterizable.parameterizable import CLASSNAME_PARAM_KEY


def test_override_get_default_params():
    _known_parameterizable_classes.clear()

    # Track if __init__ was called
    init_called = [False]

    class ClassWithSideEffects(ParameterizableClass):
        def __init__(self, param1=10, param2="default"):
            super().__init__()
            self.param1 = param1
            self.param2 = param2
            # Side effect: modify external state
            init_called[0] = True

        def get_params(self):
            return {
                "param1": self.param1,
                "param2": self.param2
            }

        @classmethod
        def get_default_params(cls):
            # Override to avoid creating an instance
            return {
                "param1": 10,
                "param2": "default"
            }

    # Test that get_default_params doesn't create an instance
    init_called[0] = False
    default_params = ClassWithSideEffects.get_default_params()
    assert not init_called[0]  # __init__ should not be called
    assert default_params == {"param1": 10, "param2": "default"}

    # Test that __get_portable_default_params__ doesn't create an instance
    init_called[0] = False
    portable_default_params = ClassWithSideEffects.__get_portable_default_params__()
    assert not init_called[0]  # __init__ should not be called
    assert portable_default_params[CLASSNAME_PARAM_KEY] == "ClassWithSideEffects"
    assert portable_default_params["param1"] == 10
    assert portable_default_params["param2"] == "default"

    _known_parameterizable_classes.clear()