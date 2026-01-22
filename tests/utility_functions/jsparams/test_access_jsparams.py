import json
import pytest

from mixinforge.utility_functions.json_processor import dumpjs, access_jsparams


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


def test_access_jsparams_invalid_json_root():
    """Test that access_jsparams raises KeyError when JSON root is not a dict."""
    # Create invalid JSON (a list at root level)
    invalid_js = json.dumps([1, 2, 3])

    with pytest.raises(KeyError, match="Invalid structure: JSON root must be a dictionary"):
        access_jsparams(invalid_js, "x")


def test_access_jsparams_non_string_input_raises_typeerror():
    """Raise TypeError when jsparams is not a string."""
    with pytest.raises(TypeError, match="jsparams"):
        access_jsparams(None, "x")


@pytest.mark.parametrize("invalid_input", [
    None,
    123,
    ["list"],
    {"dict": "value"},
    b"bytes",
])
def test_access_jsparams_various_non_string_inputs_raise_typeerror(invalid_input):
    """Various non-string inputs should raise TypeError."""
    with pytest.raises(TypeError):
        access_jsparams(invalid_input, "x")
