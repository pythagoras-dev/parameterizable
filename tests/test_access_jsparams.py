import pytest

from parameterizable.json_processor import dumpjs, loadjs, access_jsparams


class ParamObj:
    def __init__(self, x=0, y="", z=None, cfg=None):
        self.x = x
        self.y = y
        self.z = z
        self.cfg = cfg

    def get_params(self):
        # Only parameters returned here are serialized into the JSON under PARAMS->DICT
        return {"x": self.x, "y": self.y, "z": self.z, "cfg": self.cfg}


def test_access_jsparams_returns_selected_params():
    o = ParamObj(x=10, y="foo", z=3)
    js = dumpjs(o)

    result = access_jsparams(js, "x", "y")

    assert result == {"x": 10, "y": "foo"}


def test_access_jsparams_with_nested_values():
    nested_list = [1, 2, [3, 4], "ok"]
    o = ParamObj(x=1, y="a", cfg=nested_list)
    js = dumpjs(o)

    result = access_jsparams(js, "cfg")

    # access_jsparams returns JSON-native structures directly
    assert result == {"cfg": nested_list}


def test_access_jsparams_missing_key_raises_keyerror():
    o = ParamObj(x=2, y="b")
    js = dumpjs(o)

    with pytest.raises(KeyError):
        access_jsparams(js, "missing")


def test_access_jsparams_invalid_structure_raises_keyerror():
    # Use dumps on a plain dict — it won't contain PARAMS->DICT structure
    js = dumpjs({"plain": 1})

    with pytest.raises(KeyError):
        access_jsparams(js, "x")
