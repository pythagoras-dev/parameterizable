import json
import types
import builtins
import pytest

from enum import Enum

from parameterizable.json_processor import (
    _collect_object_state,
    _to_serializable_dict,
    _process_state,
    _recreate_object,
    _from_serializable_dict,
    dumps,
    loads,
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


class _SingleSlot:
    __slots__ = "x"

    def __init__(self, x=5):
        self.x = x


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


class NewSlots:
    __slots__ = ("z",)

    def __init__(self, z=1):
        self.z = z


def test_collect_object_state_dict_only():
    obj = DictOnly()
    out = _collect_object_state(obj)
    assert out == {"x": 10, "y": "hi"}


def test_collect_object_state_slots_and_inheritance():
    h = Hybrid()
    out = _collect_object_state(h)
    # Must include slots from class and base and __dict__ attrs
    assert out["s"] == 42
    assert out["base"] == "base"
    assert out["d"] == "present in __dict__"


def test_collect_object_state_ignores_missing_slots():
    s = SlotsOnly.__new__(SlotsOnly)  # skip __init__ so slots not set
    out = _collect_object_state(s)
    # missing slots should be ignored rather than raising
    assert out == {}


def test_collect_object_state_single_string_slot():
    obj = _SingleSlot(7)
    state = _collect_object_state(obj)
    assert state == {"x": 7}


def test_collect_object_state_ignores_weakref():
    obj = WithWeakref(5)
    out = _collect_object_state(obj)
    assert out == {"a": 5}


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
    # tuple/set/dict should be marked appropriately
    assert set(out.keys()) == {"t", "s", "d", "l"}
    assert _Markers.TUPLE in out["t"]
    assert _Markers.SET in out["s"]
    assert _Markers.DICT in out["d"]
    # lists remain lists recursively
    assert out["l"] == [1, 2, 3]


def test_plain_string_key_dict_not_wrapped():
    data = {"a": 1, "b": (2, 3)}
    out = _to_serializable_dict(data)
    # Should remain a plain dict (no ...DICT... marker) when all keys are strings
    assert isinstance(out, dict)
    assert _Markers.DICT not in out
    # Tuples inside should still be marked
    assert out["b"] == {_Markers.TUPLE: [2, 3]}


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
    assert gp_out[_Markers.PARAMS]["a"] == 7
    # Ensure state converted recursively
    assert st_out[_Markers.STATE]["v"] == 99


def test_to_serializable_get_params_has_precedence_over_getstate():
    obj = GetParamsAndState(a=10, b=20)
    ser = _to_serializable_dict(obj)

    assert _Markers.PARAMS in ser
    assert _Markers.STATE not in ser
    assert ser[_Markers.PARAMS] == {"a": 10}

    reconstructed = _from_serializable_dict(ser)
    assert isinstance(reconstructed, GetParamsAndState)
    assert reconstructed.a == 10
    # b will have its default value because it wasn't in PARAMS
    assert reconstructed.b == "z"


class SelfRefer:
    pass


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


def test_process_state_wraps_metadata_and_recurses():
    obj = GetParams(1, "x")
    state = {"k": (1, 2)}
    wrapped = _process_state(state, obj, _Markers.STATE, set())
    assert wrapped[_Markers.CLASS] == "GetParams"
    assert wrapped[_Markers.MODULE] == __name__
    # inner tuple should have been converted to marker
    assert wrapped[_Markers.STATE]["k"] == {_Markers.TUPLE: [1, 2]}


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


def test_recreate_object_via_state_fallback_fails_on_undeclared_attribute():
    # NewSlots has no __setstate__ and no __dict__, so it cannot be assigned
    # attributes that are not in its __slots__ during fallback reconstruction.
    serialized = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "NewSlots",
        _Markers.STATE: {"z": 1, "undeclared": 2},
    }
    with pytest.raises(AttributeError):
        _recreate_object(serialized)


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
    ser = dumps(obj)
    back = loads(ser)
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
    s = dumps(obj, indent=2, sort_keys=True)
    # should be valid JSON with newlines/indentation due to indent
    assert isinstance(s, str) and "\n" in s and "  " in s

    loaded = loads(s)
    assert loaded["msg"] == "hello"
    assert loaded["nums"] == (1, 2, 3)
    assert loaded["enum"] is Color.GREEN
    assert isinstance(loaded["inner"], GetParams)
    assert loaded["inner"].a == 2
    assert loaded["inner"].b == "ok"


def test_loads_forbids_object_hook_and_invalid_json():
    with pytest.raises(ValueError):
        loads("{}", object_hook=lambda d: d)
    with pytest.raises(json.JSONDecodeError):
        loads("not a json")