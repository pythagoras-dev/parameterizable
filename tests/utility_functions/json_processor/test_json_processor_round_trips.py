"""Round-trip tests for json_processor serialization and deserialization.

This module tests the complete serialize-deserialize cycle for various
object types including primitives, containers, enums, and custom objects.
"""
import json
import pytest

from enum import Enum

from mixinforge.utility_functions.json_processor import (
    _to_serializable_dict,
    _from_serializable_dict,
    dumpjs,
    loadjs,
    _Markers,
)


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class DictOnly:
    def __init__(self):
        self.x = 10
        self.y = "hi"


class SlotsOnly:
    __slots__ = ("a", "b")

    def __init__(self, a=1, b=2):
        self.a = a
        self.b = b


class BaseSlots:
    __slots__ = ("base",)

    def __init__(self):
        self.base = "base"


class Hybrid(BaseSlots):
    __slots__ = ("__dict__", "s")

    def __init__(self):
        super().__init__()
        self.s = 42
        self.d = "present in __dict__"


class BadStateTuple(BaseSlots):
    def __getstate__(self):
        return 1, 2, 3


class GetParams:
    def __init__(self, a=3, b="z"):
        self.a = a
        self.b = b

    def get_params(self):
        return {"a": self.a, "b": self.b}


class GetState:
    def __init__(self, v):
        self._v = v

    def __getstate__(self):
        return {"v": self._v}

    def __setstate__(self, state):
        self._v = state["v"]


class SlottedGetstateDict:
    __slots__ = ("val",)

    def __init__(self, val):
        self.val = val

    def __getstate__(self):
        return {"val": self.val}


class StateNoSetState:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __getstate__(self):
        return {"a": 111, "b": 222}


class WithWeakref:
    __slots__ = ("a", "__weakref__")

    def __init__(self, a=1):
        self.a = a


def test_round_trip_dict_only():
    obj = DictOnly()
    ser = dumpjs(obj)
    back = loadjs(ser)
    assert isinstance(back, DictOnly)
    assert back.x == 10
    assert back.y == "hi"


def test_round_trip_slotted_with_getstate_dict():
    obj = SlottedGetstateDict(101)
    ser = dumpjs(obj)
    back = loadjs(ser)
    assert isinstance(back, SlottedGetstateDict)
    assert back.val == 101


def test_round_trip_hybrid_slots_and_dict():
    obj = Hybrid()
    obj.base = "new base"
    obj.s = 99
    obj.d = "new dict val"
    obj.extra = "another dict val"

    ser = dumpjs(obj)
    back = loadjs(ser)

    assert isinstance(back, Hybrid)
    assert back.base == "new base"
    assert back.s == 99
    assert back.d == "new dict val"
    assert back.extra == "another dict val"


def test_round_trip_with_weakref():
    obj = WithWeakref(a=10)
    ser = dumpjs(obj)
    back = loadjs(ser)
    assert isinstance(back, WithWeakref)
    assert back.a == 10


def test_recreate_from_malformed_tuple_state_raises():
    obj = BadStateTuple()
    serialized = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "BadStateTuple",
        _Markers.STATE: _to_serializable_dict(obj.__getstate__()),
    }

    with pytest.raises(TypeError, match="Tuple state length .* does not match"):
        _from_serializable_dict(serialized)


def test_recreate_from_cpython_getstate_tuple_format():
    """Verify reconstruction from CPython's (dict, slots) tuple state format."""
    obj = Hybrid()
    obj.base = "b"
    obj.s = 1
    obj.d = 2

    state_tuple = ({"d": 2}, {"base": "b", "s": 1})

    serialized_payload = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "Hybrid",
        _Markers.STATE: _to_serializable_dict(state_tuple),
    }

    reconstructed = _from_serializable_dict(serialized_payload)

    assert isinstance(reconstructed, Hybrid)
    assert reconstructed.base == "b"
    assert reconstructed.s == 1
    assert reconstructed.d == 2


@pytest.mark.parametrize(
    "obj, equals",
    [
        (None, lambda a, b: a is b),
        (True, lambda a, b: a is b),
        (0, lambda a, b: a == b),
        (3.14, lambda a, b: a == b),
        ("abc", lambda a, b: a == b),
        ([1, 2, 3], lambda a, b: a == b),
        ((1, 2, 3), lambda a, b: a == b),
        ({1, 2, 3}, lambda a, b: a == b),
        ({"a": 1, "b": (2, 3)}, lambda a, b: a == b),
        ({1: "a", 2: "b"}, lambda a, b: a == b),
        ({"a": 1, 2: "b"}, lambda a, b: a == b),
        (Color.RED, lambda a, b: a is b),
    ],
)
def test_round_trip_matrix(obj, equals):
    ser = _to_serializable_dict(obj)
    back = _from_serializable_dict(ser)
    assert equals(obj, back)


def test_from_serializable_round_trip_complex():
    complex_obj = {
        (1, 2): {"a": [1, 2, {3, 4}]},
        "enum": Color.RED,
        "obj": GetParams(8, "q"),
    }
    ser = _to_serializable_dict(complex_obj)
    de = _from_serializable_dict(ser)
    assert (1, 2) in de
    assert de["enum"] is Color.RED
    assert isinstance(de["obj"], GetParams)
    assert de["obj"].a == 8 and de["obj"].b == "q"
    assert de[(1, 2)]["a"][2] == {3, 4}


def test_round_trip_custom_objects_both_variants():
    gp = GetParams(7, "z")
    gp_ser = _to_serializable_dict(gp)
    gp_back = _from_serializable_dict(gp_ser)
    assert isinstance(gp_back, GetParams)
    assert gp_back.a == 7 and gp_back.b == "z"

    gs = GetState(123)
    gs_ser = _to_serializable_dict(gs)
    gs_back = _from_serializable_dict(gs_ser)
    assert isinstance(gs_back, GetState)
    assert gs_back._v == 123


def test_round_trip_slots_only():
    obj = SlotsOnly(a=10, b=20)
    ser = dumpjs(obj)
    back = loadjs(ser)
    assert isinstance(back, SlotsOnly)
    assert back.a == 10
    assert back.b == 20


def test_mixed_key_dict_uses_DICT_marker_and_round_trips():
    data = {"a": 1, 2: (3, 4)}
    ser = _to_serializable_dict(data)
    assert isinstance(ser, dict) and _Markers.DICT in ser
    back = _from_serializable_dict(ser)
    assert back == {"a": 1, 2: (3, 4)}


@pytest.mark.parametrize(
    "payload",
    [
        {_Markers.TUPLE: [1, 2], "extra": 1},
        {_Markers.SET: [1, 2], "extra": 1},
        {_Markers.DICT: [], "extra": 1},
    ],
)
def test_from_serializable_marker_exclusive_key_violation(payload):
    with pytest.raises(TypeError):
        _from_serializable_dict(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {_Markers.TUPLE: 123},
        {_Markers.SET: 123},
        {_Markers.DICT: 123},
        {_Markers.DICT: [[1, 2, 3]]},
    ],
)
def test_from_serializable_marker_value_type_violation(payload):
    with pytest.raises(TypeError):
        _from_serializable_dict(payload)


def test_dumps_and_loads_round_trip_json_string_with_kwargs():
    obj = {
        "msg": "hello",
        "nums": (1, 2, 3),
        "enum": Color.GREEN,
        "inner": GetParams(2, "ok"),
    }
    s = dumpjs(obj, indent=2, sort_keys=True)
    assert isinstance(s, str) and "\n" in s and "  " in s

    loaded = loadjs(s)
    assert loaded["msg"] == "hello"
    assert loaded["nums"] == (1, 2, 3)
    assert loaded["enum"] is Color.GREEN
    assert isinstance(loaded["inner"], GetParams)
    assert loaded["inner"].a == 2
    assert loaded["inner"].b == "ok"


def test_loads_forbids_object_hook_and_invalid_json():
    with pytest.raises(ValueError):
        loadjs("{}", object_hook=lambda d: d)
    with pytest.raises(json.JSONDecodeError):
        loadjs("not a json")


def test_loadjs_non_string_input_raises_typeerror():
    """Raise TypeError when loadjs input is not a string."""
    with pytest.raises(TypeError, match="s"):
        loadjs(None)


@pytest.mark.parametrize("invalid_input", [
    None,
    123,
    12.5,
    ["list"],
    {"dict": "value"},
    b"bytes",
])
def test_loadjs_various_non_string_inputs_raise_typeerror(invalid_input):
    """Various non-string inputs should raise TypeError."""
    with pytest.raises(TypeError):
        loadjs(invalid_input)
