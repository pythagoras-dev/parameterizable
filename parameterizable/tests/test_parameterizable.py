from parameterizable.parameterizable import *
from parameterizable.parameterizable import _known_parameterizable_classes
from parameterizable.parameterizable import _smoketest_parameterizable_class
from parameterizable.parameterizable import _smoketest_known_parameterizable_classes
from parameterizable.parameterizable import CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY
import pytest
from abc import *

class GoodPameterizable(ABC, ParameterizableClass):
    def __init__(self, a: int = 10, b: str = "hello", c=int):
        ParameterizableClass.__init__(self)
        self.a = a
        self.b = b
        self.c = c

    def get_params(self) -> dict[str, Any]:
        params = dict(a=self.a, b=self.b, c=self.c)
        return params


def test_good_class():
    _known_parameterizable_classes.clear()
    assert is_parameterizable(GoodPameterizable)
    assert _smoketest_parameterizable_class(GoodPameterizable)
    assert len(_known_parameterizable_classes) == 1
    register_parameterizable_class(GoodPameterizable)
    assert len(_known_parameterizable_classes) == 1
    obj = GoodPameterizable()
    obj.a = -12345
    obj.b = "Hi!"
    obj.c = str
    params = obj.__get_portable_params__()
    assert params["a"] == -12345
    assert params["b"] == "Hi!"
    assert type(params["c"]) == dict
    obj2 = get_object_from_portable_params(params)
    assert obj2.a == -12345
    assert obj2.b == "Hi!"
    assert obj2.c == str
    _known_parameterizable_classes.clear()

class EvenBetterOne(GoodPameterizable):
    def __init__(self, a: int = 10, b: str = "hello", c=int, d: float = 3.14):
        GoodPameterizable.__init__(self, a, b, c)
        self.d = d

    def get_params(self) -> dict[str, Any]:
        params = super().get_params()
        params["d"] = self.d
        return params

def test_even_better_one():
    _known_parameterizable_classes.clear()
    x = EvenBetterOne()
    assert len(_known_parameterizable_classes) == 1
    _known_parameterizable_classes.clear()


class EmptyClass:
    pass

def test_empty_class():
    assert not is_parameterizable(EmptyClass)


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


def test_builtin_types_in_portable_params():
    _known_parameterizable_classes.clear()

    class TypeTester(ParameterizableClass):
        def __init__(self, int_val=42, float_val=3.14, str_val="test", 
                     bool_val=True, none_val=None, list_val=None, dict_val=None):
            super().__init__()
            self.int_val = int_val
            self.float_val = float_val
            self.str_val = str_val
            self.bool_val = bool_val
            self.none_val = none_val
            self.list_val = list_val if list_val is not None else [1, 2, 3]
            self.dict_val = dict_val if dict_val is not None else {"a": 1, "b": 2}

        def get_params(self):
            return {
                "int_val": self.int_val,
                "float_val": self.float_val,
                "str_val": self.str_val,
                "bool_val": self.bool_val,
                "none_val": self.none_val,
                "list_val": self.list_val,
                "dict_val": self.dict_val
            }

    obj = TypeTester()
    params = obj.__get_portable_params__()

    # Check that all values are preserved correctly
    assert params["int_val"] == 42
    assert params["float_val"] == 3.14
    assert params["str_val"] == "test"
    assert params["bool_val"] is True
    assert params["none_val"] is None
    assert params["list_val"] == [1, 2, 3]
    assert params["dict_val"] == {"a": 1, "b": 2}

    # Recreate object from portable params
    obj2 = get_object_from_portable_params(params)
    assert obj2.int_val == 42
    assert obj2.float_val == 3.14
    assert obj2.str_val == "test"
    assert obj2.bool_val is True
    assert obj2.none_val is None
    assert obj2.list_val == [1, 2, 3]
    assert obj2.dict_val == {"a": 1, "b": 2}

    _known_parameterizable_classes.clear()


def test_smoketest_known_parameterizable_classes():
    _known_parameterizable_classes.clear()

    # Register multiple parameterizable classes
    register_parameterizable_class(GoodPameterizable)
    register_parameterizable_class(EvenBetterOne)

    # Test that smoketest runs without errors
    _smoketest_known_parameterizable_classes()

    _known_parameterizable_classes.clear()


def test_get_object_from_portable_params_errors():
    # Test with non-dictionary input
    with pytest.raises(AssertionError):
        get_object_from_portable_params("not a dict")

    # Test with dictionary missing required keys
    with pytest.raises(AssertionError):
        get_object_from_portable_params({})

    # Test with unknown class name
    with pytest.raises(KeyError):
        get_object_from_portable_params({CLASSNAME_PARAM_KEY: "NonExistentClass"})

    # Test with invalid builtin type dictionary
    with pytest.raises(AssertionError):
        get_object_from_portable_params({
            BUILTIN_TYPE_KEY: "__builtins__.int",
            "extra_key": "should not be here"
        })


class UnsupportedTypeClass(ParameterizableClass):
    def __init__(self):
        super().__init__()
        self.unsupported = object()  # object() is not a supported type

    def get_params(self):
        return {"unsupported": self.unsupported}


def test_unsupported_type_error():
    obj = UnsupportedTypeClass()

    # Test that __get_portable_params__ raises ValueError for unsupported types
    with pytest.raises(ValueError, match="Unsupported type"):
        obj.__get_portable_params__()


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


def test_nested_parameterizable_objects():
    _known_parameterizable_classes.clear()

    class NestedContainer(ParameterizableClass):
        def __init__(self, nested_obj=None):
            super().__init__()
            self.nested_obj = nested_obj if nested_obj else GoodPameterizable()

        def get_params(self):
            return {"nested_obj": self.nested_obj}

    # Create a container with a nested parameterizable object
    inner_obj = GoodPameterizable(a=100, b="nested", c=float)
    container = NestedContainer(inner_obj)

    # Convert to portable params
    portable_params = container.__get_portable_params__()

    # Check that the nested object is properly converted
    assert CLASSNAME_PARAM_KEY in portable_params["nested_obj"]
    assert portable_params["nested_obj"][CLASSNAME_PARAM_KEY] == "GoodPameterizable"
    assert portable_params["nested_obj"]["a"] == 100
    assert portable_params["nested_obj"]["b"] == "nested"

    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)

    # Check that the nested object is properly reconstructed
    assert isinstance(reconstructed.nested_obj, GoodPameterizable)
    assert reconstructed.nested_obj.a == 100
    assert reconstructed.nested_obj.b == "nested"
    assert reconstructed.nested_obj.c == float

    _known_parameterizable_classes.clear()
