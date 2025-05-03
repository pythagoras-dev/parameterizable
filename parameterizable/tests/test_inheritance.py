from parameterizable.parameterizable import *
from parameterizable.parameterizable import _known_parameterizable_classes
import pytest


def test_inheritance_and_overriding():
    _known_parameterizable_classes.clear()

    class BaseParamClass(ParameterizableClass):
        def __init__(self, base_param=10):
            super().__init__()
            self.base_param = base_param

        def get_params(self):
            return {"base_param": self.base_param}

    class DerivedParamClass(BaseParamClass):
        def __init__(self, base_param=10, derived_param=20):
            super().__init__(base_param)
            self.derived_param = derived_param

        def get_params(self):
            params = super().get_params()
            params["derived_param"] = self.derived_param
            return params

    # Test that both classes are parameterizable
    assert is_parameterizable(BaseParamClass)
    assert is_parameterizable(DerivedParamClass)

    # Test parameter inheritance
    base = BaseParamClass(15)
    derived = DerivedParamClass(15, 25)

    base_params = base.get_params()
    derived_params = derived.get_params()

    assert base_params == {"base_param": 15}
    assert derived_params == {"base_param": 15, "derived_param": 25}

    # Test portable params and reconstruction
    base_portable = base.__get_portable_params__()
    derived_portable = derived.__get_portable_params__()

    reconstructed_base = get_object_from_portable_params(base_portable)
    reconstructed_derived = get_object_from_portable_params(derived_portable)

    assert reconstructed_base.base_param == 15
    assert reconstructed_derived.base_param == 15
    assert reconstructed_derived.derived_param == 25

    _known_parameterizable_classes.clear()