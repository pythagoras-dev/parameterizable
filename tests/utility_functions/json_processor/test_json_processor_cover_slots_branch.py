from mixinforge.utility_functions.json_processor import _to_serializable_dict, _recreate_object, _Markers


class SlotsMaskGetstate:
    __slots__ = ("x",)

    def __init__(self, x):
        self.x = x

    # Make hasattr(inst, "__getstate__") return False even if CPython provides a default
    def __getattribute__(self, name):
        if name == "__getstate__":
            raise AttributeError
        return object.__getattribute__(self, name)


class HybridSlotsMaskGetstate:
    __slots__ = ("__dict__", "y")

    def __init__(self, y):
        self.y = y
        self.extra = "e"

    def __getattribute__(self, name):
        if name == "__getstate__":
            raise AttributeError
        return object.__getattribute__(self, name)


def test_slots_only_branch_is_used_when_getstate_hidden():
    obj = SlotsMaskGetstate(123)
    ser = _to_serializable_dict(obj)

    # Ensure slots path produced a STATE payload
    assert _Markers.STATE in ser

    back = _recreate_object(ser)
    assert isinstance(back, SlotsMaskGetstate)
    assert back.x == 123


def test_hybrid_slots_branch_is_used_when_getstate_hidden():
    obj = HybridSlotsMaskGetstate(5)
    obj.more = 42

    ser = _to_serializable_dict(obj)
    assert _Markers.STATE in ser

    back = _recreate_object(ser)
    assert isinstance(back, HybridSlotsMaskGetstate)
    assert back.y == 5
    assert back.extra == "e"
    assert back.more == 42
