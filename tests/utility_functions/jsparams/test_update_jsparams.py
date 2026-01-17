import json
import pytest

from mixinforge.utility_functions.json_processor import dumpjs, loadjs, update_jsparams


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


def test_update_jsparams_invalid_json_root():
    """Test that update_jsparams raises KeyError when JSON root is not a dict."""
    # Create invalid JSON (a list at root level)
    invalid_js = json.dumps([1, 2, 3])

    with pytest.raises(KeyError, match="Invalid structure: JSON root must be a dictionary"):
        update_jsparams(invalid_js, x=5)


def test_update_jsparams_non_string_input_raises_typeerror():
    """Raise TypeError when jsparams is not a string."""
    with pytest.raises(TypeError, match="jsparams"):
        update_jsparams(None, x=5)


@pytest.mark.parametrize("invalid_input", [
    None,
    123,
    ["list"],
    {"dict": "value"},
    b"bytes",
])
def test_update_jsparams_various_non_string_inputs_raise_typeerror(invalid_input):
    """Various non-string inputs should raise TypeError."""
    with pytest.raises(TypeError):
        update_jsparams(invalid_input, x=5)

