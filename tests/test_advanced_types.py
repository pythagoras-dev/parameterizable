"""Tests for advanced type handling in parameterizable classes.

This module tests edge cases and advanced type handling functionality:
- Type objects as parameters
- Complex nested collections
- All supported built-in types
- Edge cases like empty collections and special values
"""

from src.parameterizable.parameterizable import (
    ParameterizableClass,
    get_object_from_portable_params,
    BUILTIN_TYPE_KEY,
    _known_parameterizable_classes
)
from tests.fixtures import basic_parameterizable_class


def test_type_objects_as_parameters(basic_parameterizable_class):
    """Test that type objects (like int, str) can be used as parameters."""

    # Ensure the registry is clear
    _known_parameterizable_classes.clear()

    # Create an object with type objects as parameters
    obj = basic_parameterizable_class(param1=10, param2="test", param3=dict)

    # Convert to portable params
    portable_params = obj.__get_portable_params__()

    # Check that the type object is properly converted
    assert isinstance(portable_params["param3"], dict)
    assert BUILTIN_TYPE_KEY in portable_params["param3"]
    assert portable_params["param3"][BUILTIN_TYPE_KEY] == "__builtins__.dict"

    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)

    # Check that the type object is properly reconstructed
    assert reconstructed.param3 == dict


def test_all_supported_builtin_types():
    """Test all supported built-in types."""

    # Ensure the registry is clear
    _known_parameterizable_classes.clear()

    class AllTypesClass(ParameterizableClass):
        def __init__(self, int_val=42, float_val=3.14, str_val="test", bool_val=True,
                     complex_val=complex(1, 2), list_val=None, tuple_val=None,
                     dict_val=None, set_val=None, frozenset_val=None, type_val=int,
                     none_val=None):
            super().__init__()
            # Create an attribute for each supported built-in type
            self.int_val = int_val
            self.float_val = float_val
            self.str_val = str_val
            self.bool_val = bool_val
            self.complex_val = complex_val
            self.list_val = list_val if list_val is not None else [1, 2, 3]
            self.tuple_val = tuple_val if tuple_val is not None else (1, 2, 3)
            self.dict_val = dict_val if dict_val is not None else {"a": 1, "b": 2}
            self.set_val = set_val if set_val is not None else {1, 2, 3}
            self.frozenset_val = frozenset_val if frozenset_val is not None else frozenset([1, 2, 3])
            self.type_val = type_val
            self.none_val = none_val

        def get_params(self):
            return {
                "int_val": self.int_val,
                "float_val": self.float_val,
                "str_val": self.str_val,
                "bool_val": self.bool_val,
                "complex_val": self.complex_val,
                "list_val": self.list_val,
                "tuple_val": self.tuple_val,
                "dict_val": self.dict_val,
                "set_val": self.set_val,
                "frozenset_val": self.frozenset_val,
                "type_val": self.type_val,
                "none_val": self.none_val
            }

    # Create an object with all supported types
    obj = AllTypesClass()

    # Convert to portable params
    portable_params = obj.__get_portable_params__()

    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)

    # Check that all values are preserved correctly
    assert reconstructed.int_val == 42
    assert reconstructed.float_val == 3.14
    assert reconstructed.str_val == "test"
    assert reconstructed.bool_val is True
    assert reconstructed.complex_val == complex(1, 2)
    assert reconstructed.list_val == [1, 2, 3]
    assert reconstructed.tuple_val == (1, 2, 3)
    assert reconstructed.dict_val == {"a": 1, "b": 2}
    assert reconstructed.set_val == {1, 2, 3}
    assert reconstructed.frozenset_val == frozenset([1, 2, 3])
    assert reconstructed.type_val == int
    assert reconstructed.none_val is None


def test_complex_nested_collections():
    """Test complex nested collections like lists of lists and dicts of dicts."""

    # Ensure the registry is clear
    _known_parameterizable_classes.clear()

    class ComplexCollectionsClass(ParameterizableClass):
        def __init__(self, nested_list=None, nested_dict=None):
            super().__init__()
            # Create complex nested collections
            self.nested_list = nested_list if nested_list is not None else [
                [1, 2, 3],
                ["a", "b", "c"],
                [True, False]
            ]
            self.nested_dict = nested_dict if nested_dict is not None else {
                "numbers": {"one": 1, "two": 2, "three": 3},
                "strings": {"a": "apple", "b": "banana", "c": "cherry"},
                "booleans": {"true": True, "false": False}
            }

        def get_params(self):
            return {
                "nested_list": self.nested_list,
                "nested_dict": self.nested_dict
            }

    # Create an object with complex nested collections
    obj = ComplexCollectionsClass()

    # Convert to portable params
    portable_params = obj.__get_portable_params__()

    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)

    # Check that all values are preserved correctly
    assert reconstructed.nested_list == [
        [1, 2, 3],
        ["a", "b", "c"],
        [True, False]
    ]
    assert reconstructed.nested_dict == {
        "numbers": {"one": 1, "two": 2, "three": 3},
        "strings": {"a": "apple", "b": "banana", "c": "cherry"},
        "booleans": {"true": True, "false": False}
    }


def test_edge_cases():
    """Test edge cases like empty collections and special values."""

    # Ensure the registry is clear
    _known_parameterizable_classes.clear()

    class EdgeCasesClass(ParameterizableClass):
        def __init__(self, empty_list=None, empty_dict=None, empty_string="",
                     zero=0, large_int=10**20, special_float=float('inf')):
            super().__init__()
            # Create edge cases
            self.empty_list = empty_list if empty_list is not None else []
            self.empty_dict = empty_dict if empty_dict is not None else {}
            self.empty_string = empty_string
            self.zero = zero
            self.large_int = large_int
            self.special_float = special_float

        def get_params(self):
            return {
                "empty_list": self.empty_list,
                "empty_dict": self.empty_dict,
                "empty_string": self.empty_string,
                "zero": self.zero,
                "large_int": self.large_int,
                "special_float": self.special_float
            }

    # Create an object with edge cases
    obj = EdgeCasesClass()

    # Convert to portable params
    portable_params = obj.__get_portable_params__()

    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)

    # Check that all values are preserved correctly
    assert reconstructed.empty_list == []
    assert reconstructed.empty_dict == {}
    assert reconstructed.empty_string == ""
    assert reconstructed.zero == 0
    assert reconstructed.large_int == 10**20
    assert reconstructed.special_float == float('inf')