import pytest

from parameterizable.json_processor import dumpjs, loadjs, update_jsparams


class ParamObj:
    def __init__(self, x=0, y="", z=None, cfg=None):
        self.x = x
        self.y = y
        self.z = z
        self.cfg = cfg

    def get_params(self):
        # Only parameters returned here are serialized into the JSON under PARAMS->DICT
        return {"x": self.x, "y": self.y, "z": self.z, "cfg": self.cfg}


def test_update_jsparams_replaces_existing_param():
    o = ParamObj(x=1, y="a")
    js = dumpjs(o)

    js_updated = update_jsparams(js, x=5)
    o2 = loadjs(js_updated)

    assert isinstance(o2, ParamObj)
    assert o2.x == 5  # replaced
    assert o2.y == "a"  # unchanged
    assert o2.z is None


def test_update_jsparams_adds_new_param():
    # Start with object missing z (None); then add z via update
    o = ParamObj(x=2, y="b")
    js = dumpjs(o)

    js_updated = update_jsparams(js, z=99)
    o2 = loadjs(js_updated)

    assert o2.z == 99
    assert o2.x == 2 and o2.y == "b"


def test_update_jsparams_nested_values_roundtrip():
    o = ParamObj(x=3, y="c")
    js = dumpjs(o)

    # nested list is supported directly by the loader; nested dicts would require internal DICT markers
    nested_list = [1, 2, [3, 4], "ok"]
    js_updated = update_jsparams(js, cfg=nested_list)
    o2 = loadjs(js_updated)

    assert o2.cfg == nested_list


