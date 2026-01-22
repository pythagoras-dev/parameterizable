import pytest

from mixinforge.utility_functions.json_processor import (
    _to_serializable_dict,
    _from_serializable_dict,
    _Markers,
)


class StrSlots:
    __slots__ = "w"

    def __init__(self, w):
        self.w = w


class TwoSlots:
    __slots__ = ("u", "v")

    def __init__(self, u=0, v=0):
        self.u = u
        self.v = v


def test_to_from_with_string_slots():
    obj = StrSlots("hello")
    ser = _to_serializable_dict(obj)
    back = _from_serializable_dict(ser)
    assert isinstance(back, StrSlots)
    assert back.w == "hello"


def test_recreate_object_tuple_state_swapped_components():
    # Craft state where first element is dict_values and second is slot values list
    state_tuple = ({}, [10, 20])
    payload = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "TwoSlots",
        _Markers.STATE: _to_serializable_dict(state_tuple),
    }
    back = _from_serializable_dict(payload)
    assert isinstance(back, TwoSlots)
    assert back.u == 10 and back.v == 20


def test_recreate_object_tuple_state_fallback_pair_becomes_slots():
    # Neither element is dict or list/tuple, so fallback treats entire state as slot values
    state_tuple = (1, 2)
    payload = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "TwoSlots",
        _Markers.STATE: _to_serializable_dict(state_tuple),
    }
    back = _from_serializable_dict(payload)
    assert isinstance(back, TwoSlots)
    assert back.u == 1 and back.v == 2


def test_from_serializable_plain_dict_is_unsupported():
    with pytest.raises(TypeError):
        _from_serializable_dict({"a": 1, "b": 2})

