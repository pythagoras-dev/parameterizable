from parameterizable.parameterizable import *
from parameterizable.parameterizable import _known_parameterizable_classes
import pytest


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
    params = obj.get_portable_params()

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


class UnsupportedTypeClass(ParameterizableClass):
    def __init__(self):
        super().__init__()
        self.unsupported = object()  # object() is not a supported type

    def get_params(self):
        return {"unsupported": self.unsupported}


def test_unsupported_type_error():
    obj = UnsupportedTypeClass()

    # Test that get_portable_params raises ValueError for unsupported types
    with pytest.raises(ValueError, match="Unsupported type"):
        obj.get_portable_params()