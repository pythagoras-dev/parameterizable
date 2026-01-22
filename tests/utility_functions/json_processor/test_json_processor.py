import types
import builtins
import pytest

from enum import Enum

from mixinforge.utility_functions.json_processor import (
    _to_serializable_dict,
    _recreate_object,
    _from_serializable_dict,
    _Markers,
)


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


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
        (lambda: (lst := [], lst.append(lst)), "list"),
        (lambda: (d := {}, d.update({"d": d})), "dict"),
        (lambda: (o := SelfRefer(), setattr(o, "me", o)), "SelfRefer"),
        (lambda: (nested_list := [{}], nested_list[0].update({"l": nested_list})), "list"),
    ],
)
def test_to_serializable_cycle_detection(obj_creator, type_name):
    obj = obj_creator()
    with pytest.raises(RecursionError):
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
