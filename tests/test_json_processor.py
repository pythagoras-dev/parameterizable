import json
import types
import builtins
import pytest

from enum import Enum

from parameterizable.json_processor import (
    _to_serializable_dict,
    _recreate_object,
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


class BadStateTuple(BaseSlots):  # has 'base' slot
    def __getstate__(self):
        # incorrect state: tuple of wrong size for slots
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
        # not used at reconstruction time
        self.a = a
        self.b = b

    def __getstate__(self):
        return {"a": 111, "b": 222}


class WithWeakref:
    __slots__ = ("a", "__weakref__")

    def __init__(self, a=1):
        self.a = a


class GetParamsAndState:
    def __init__(self, a=3, b="z"):
        self.a = a
        self.b = b

    def get_params(self):
        return {"a": self.a}

    def __getstate__(self):
        return {"b": self.b}


class SelfRefer:
    pass


@pytest.mark.parametrize(
    "value",
    [None, True, False, 0, 123, -5, 3.14, "abc"],
)
def test_to_serializable_primitives(value):
    assert _to_serializable_dict(value) == value


def test_to_serializable_containers_and_markers():
    data = {
        "t": (1, 2, 3),
        "s": {1, 2},
        "d": {1: "a", 2: "b"},
        "l": [1, 2, 3],
    }
    out = _to_serializable_dict(data)

    assert out.keys() == {_Markers.DICT}
    out_dict = {k: v for k,v in out[_Markers.DICT].items()}

    assert out_dict["t"] == {_Markers.TUPLE: [1, 2, 3]}
    assert out_dict["l"] == [1, 2, 3]
    assert out_dict["d"] == {_Markers.DICT: {1: "a", 2: "b"}}

    # For set, content matters, not order
    assert out_dict["s"].keys() == {_Markers.SET}
    assert isinstance(out_dict["s"][_Markers.SET], list)
    assert sorted(out_dict["s"][_Markers.SET]) == [1,2]


def test_to_serializable_enum():
    out = _to_serializable_dict(Color.GREEN)
    assert out[_Markers.ENUM] == "GREEN"
    assert out[_Markers.CLASS] == "Color"
    assert out[_Markers.MODULE] == __name__


def test_to_serializable_get_params_and_state_variants():
    gp = GetParams(7, "k")
    st = GetState(99)
    hy = Hybrid()

    gp_out = _to_serializable_dict(gp)
    st_out = _to_serializable_dict(st)
    hy_out = _to_serializable_dict(hy)

    for o in (gp_out, st_out, hy_out):
        assert o[_Markers.CLASS]
        assert o[_Markers.MODULE] == __name__
        assert (_Markers.PARAMS in o) ^ (_Markers.STATE in o)

    # Ensure get_params converted recursively
    assert gp_out[_Markers.PARAMS][_Markers.DICT]["a"] == 7


def test_to_serializable_get_params_has_precedence_over_getstate():
    obj = GetParamsAndState(a=10, b=20)
    ser = _to_serializable_dict(obj)

    assert _Markers.PARAMS in ser
    assert _Markers.STATE not in ser
    assert ser[_Markers.PARAMS] == {_Markers.DICT: {"a": 10}}

    reconstructed = _from_serializable_dict(ser)
    assert isinstance(reconstructed, GetParamsAndState)


@pytest.mark.parametrize(
    "obj_creator, type_name",
    [
        (lambda: (l := [], l.append(l)), "list"),
        (lambda: (d := {}, d.update({"d": d})), "dict"),
        (lambda: (o := SelfRefer(), setattr(o, "me", o)), "SelfRefer"),
        (lambda: (l := [{}], l[0].update({"l": l})), "list"),
    ],
)
def test_to_serializable_cycle_detection(obj_creator, type_name):
    obj = obj_creator()
    with pytest.raises(RecursionError, match=type_name):
        _to_serializable_dict(obj)


@pytest.mark.parametrize(
    "value",
    [
        builtins.open,  # builtin function
        len,  # builtin function (another)
        GetParams,  # a class/type
        GetParams(1, "x").__init__,  # bound method (of instance)
        (lambda x: x).__code__,  # code object
        str,  # another class/type
        types.ModuleType("m"),  # a module
    ],
)
def test_to_serializable_unsupported_types_message_includes_type(value):
    with pytest.raises(TypeError) as ei:
        _to_serializable_dict(value)
    assert type(value).__name__ in str(ei.value)


def test_recreate_object_via_params():
    obj = GetParams(5, "y")
    serialized = _to_serializable_dict(obj)
    reconstructed = _recreate_object(serialized)
    assert isinstance(reconstructed, GetParams)
    assert reconstructed.a == 5 and reconstructed.b == "y"


def test_recreate_object_via_state_with_setstate():
    obj = GetState(123)
    serialized = _to_serializable_dict(obj)
    reconstructed = _recreate_object(serialized)
    assert isinstance(reconstructed, GetState)
    assert reconstructed._v == 123


def test_recreate_object_via_state_fallback_without_setstate():
    obj = StateNoSetState(1, 2)
    serialized = _to_serializable_dict(obj)
    reconstructed = _recreate_object(serialized)
    assert isinstance(reconstructed, StateNoSetState)
    # fallback assigns attributes from state
    assert reconstructed.a == 111 and reconstructed.b == 222


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
    # Check slots
    assert back.base == "new base"
    assert back.s == 99
    # Check dict attrs
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
    # Manually serialize to inject bad state
    serialized = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "BadStateTuple",
        _Markers.STATE: _to_serializable_dict(obj.__getstate__()),
    }

    with pytest.raises(TypeError, match="Tuple state length .* does not match"):
        _from_serializable_dict(serialized)


def test_recreate_from_cpython_getstate_tuple_format():
    obj = Hybrid()
    obj.base = "b"
    obj.s = 1
    obj.d = 2  # this goes into __dict__

    # This is what obj.__getstate__() would return for a hybrid object
    # The first element is the __dict__, second is a dict of slot values
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


def test_recreate_enum_and_errors():
    enum_ser = _to_serializable_dict(Color.BLUE)
    assert _recreate_object(enum_ser) is Color.BLUE

    # not a mapping
    with pytest.raises(TypeError):
        _recreate_object([1, 2])

    # missing MODULE/CLASS
    with pytest.raises(TypeError):
        _recreate_object({_Markers.STATE: {}})

    # wrong module/class
    bad = {_Markers.MODULE: "does.not.exist", _Markers.CLASS: "X", _Markers.STATE: {}}
    with pytest.raises(ImportError):
        _recreate_object(bad)

    # class not enum when ENUM provided
    not_enum = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "GetParams",
        _Markers.ENUM: "BLUE",
    }
    with pytest.raises(TypeError):
        _recreate_object(not_enum)

    # unknown payload
    unk = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "GetParams",
        "some": 1,
    }
    with pytest.raises(TypeError):
        _recreate_object(unk)


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
        ({1: "a", 2: "b"}, lambda a, b: a == b),  # non-string keys
        ({"a": 1, 2: "b"}, lambda a, b: a == b),  # mixed keys
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
    # keys restored as tuple
    assert (1, 2) in de
    assert de["enum"] is Color.RED
    assert isinstance(de["obj"], GetParams)
    assert de["obj"].a == 8 and de["obj"].b == "q"
    # inner set restored
    assert de[(1, 2)]["a"][2] == {3, 4}


def test_round_trip_custom_objects_both_variants():
    # get_params flavor
    gp = GetParams(7, "z")
    gp_ser = _to_serializable_dict(gp)
    gp_back = _from_serializable_dict(gp_ser)
    assert isinstance(gp_back, GetParams)
    assert gp_back.a == 7 and gp_back.b == "z"

    # __getstate__/__setstate__ flavor
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
        {_Markers.DICT: [[1, 2, 3]]},  # not pairs
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
    # should be valid JSON with newlines/indentation due to indent
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