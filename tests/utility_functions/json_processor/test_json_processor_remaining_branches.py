import pytest

from mixinforge.utility_functions.json_processor import _to_serializable_dict, _recreate_object, _Markers


class Plain:
    def __init__(self):
        self.a = 1
        self.b = "x"


class PlainMaskGetstate:
    def __init__(self):
        self.a = 2
        self.b = "y"

    def __getattribute__(self, name):
        if name == "__getstate__":
            raise AttributeError
        return object.__getattribute__(self, name)


def test_plain_class_uses_dict_state_branch():
    p = PlainMaskGetstate()
    ser = _to_serializable_dict(p)
    # Should be encoded via STATE of its __dict__
    assert _Markers.STATE in ser
    back = _recreate_object(ser)
    assert isinstance(back, PlainMaskGetstate)
    assert back.a == 2 and back.b == "y"


class SlotlessMeta(type):
    def __getattribute__(cls, name):
        if name == "__slots__":
            raise AttributeError
        return super().__getattribute__(name)


class Trick(metaclass=SlotlessMeta):
    # Do not define __slots__; instances normally have __dict__, but we mask it
    def __getattribute__(self, name):
        if name == "__dict__":
            raise AttributeError
        return object.__getattribute__(self, name)


def test_unsupported_early_types_raise():
    # Functions are explicitly unsupported
    with pytest.raises(TypeError):
        _to_serializable_dict(lambda x: x)


class HideSlotsMeta(type):
    def __getattribute__(cls, name):
        if name == "__slots__":
            raise AttributeError
        return super().__getattribute__(name)


class ElseTarget(metaclass=HideSlotsMeta):
    __slots__ = ("a",)

    def __init__(self):
        self.a = 1

    def __getattribute__(self, name):
        if name in ("__dict__", "__getstate__"):
            raise AttributeError
        return object.__getattribute__(self, name)


def test_final_else_branch_raises_type_error():
    with pytest.raises(TypeError):
        _to_serializable_dict(ElseTarget())
