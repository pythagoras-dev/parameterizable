from parameterizable import *
from parameterizable import CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY
import pytest


def test_get_object_from_portable_params_errors():
    # Test with non-dictionary input
    with pytest.raises(TypeError):
        get_object_from_portable_params("not a dict")

    # Test with dictionary missing required keys
    with pytest.raises(ValueError):
        get_object_from_portable_params({})

    # Test with unknown class name
    with pytest.raises(KeyError):
        get_object_from_portable_params({CLASSNAME_PARAM_KEY: "NonExistentClass"})

    # Test with invalid builtin type dictionary
    with pytest.raises(ValueError):
        get_object_from_portable_params({
            BUILTIN_TYPE_KEY: "__builtins__.int",
            "extra_key": "should not be here"
        })
