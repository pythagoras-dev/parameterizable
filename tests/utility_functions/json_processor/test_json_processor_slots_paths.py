import json

from mixinforge.utility_functions.json_processor import (
    _to_serializable_dict,
    _recreate_object,
    _Markers,
    update_jsparams,
)


class OnlySlots:
    __slots__ = ("m", "n")

    def __init__(self, m=1, n=2):
        self.m = m
        self.n = n


class HybridSlots:
    __slots__ = ("__dict__", "p")

    def __init__(self, p=10):
        self.p = p
        self.extra = "x"


def test_to_serializable_uses_slots_branch_for_slots_only():
    obj = OnlySlots(7, 8)
    ser = _to_serializable_dict(obj)

    # Ensure we went through the slots path that emits STATE
    assert _Markers.STATE in ser

    # Ensure recreation works and populates slots
    back = _recreate_object(ser)
    assert isinstance(back, OnlySlots)
    assert back.m == 7 and back.n == 8


def test_to_serializable_uses_slots_branch_for_hybrid_and_dict_is_preserved():
    obj = HybridSlots(33)
    obj.extra = "changed"
    obj.more = 123

    ser = _to_serializable_dict(obj)
    assert _Markers.STATE in ser

    back = _recreate_object(ser)
    assert isinstance(back, HybridSlots)
    # slots applied in order
    assert back.p == 33
    # dict attributes also restored
    assert back.extra == "changed"
    assert back.more == 123


def test_update_jsparams_else_branch_on_explicit_DICT_payload():
    # Construct a JSON exactly matching the DICT marker structure to force else-branch
    params = {_Markers.DICT: {"a": 1}}
    js = json.dumps(params)
    out = update_jsparams(js, b=2)
    decoded = json.loads(out)
    # PARAMS should still be absent; DICT must carry both keys
    assert _Markers.PARAMS not in decoded
    assert decoded[_Markers.DICT] == {"a": 1, "b": 2}
