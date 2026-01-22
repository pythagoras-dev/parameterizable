
from mixinforge.utility_functions.json_processor import _from_serializable_dict, _to_serializable_dict, _Markers


class Duo:
    __slots__ = ("x", "y")

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class DuoDict:
    __slots__ = ("__dict__", "x", "y")

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


def test_tuple_state_with_slot_values_and_none():
    state_tuple = ([11, 22], None)
    payload = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "Duo",
        _Markers.STATE: _to_serializable_dict(state_tuple),
    }
    back = _from_serializable_dict(payload)
    assert isinstance(back, Duo)
    assert back.x == 11 and back.y == 22


def test_tuple_state_with_slot_values_and_dict_values():
    state_tuple = ([9, 8], {"z": 5})
    payload = {
        _Markers.MODULE: __name__,
        _Markers.CLASS: "DuoDict",
        _Markers.STATE: _to_serializable_dict(state_tuple),
    }
    back = _from_serializable_dict(payload)
    assert isinstance(back, DuoDict)
    assert back.x == 9 and back.y == 8
    assert getattr(back, "z") == 5
