import pytest

from parameterizable import ParameterizableClass
from parameterizable.json_processor import dumps


class MyParamClass(ParameterizableClass):
    def __init__(self, a=1, b="x"):
        self.a = a
        self.b = b
        self._internal = "not a param"  # should not be serialized

    def get_params(self):
        return {"a": self.a, "b": self.b}


def test_get_jsparams_and_from_jsparams_round_trip():
    obj = MyParamClass(a=10, b="hey")

    js = obj.get_jsparams()

    # Should be a JSON string (NewType[str, ...])
    assert isinstance(js, str)

    # from_jsparams is defined on the base class and should reconstruct
    restored = ParameterizableClass.from_jsparams(js)

    assert isinstance(restored, MyParamClass)
    assert restored.a == 10
    assert restored.b == "hey"

    # Attributes not returned by get_params are not serialized and thus not restored
    # They may take on default/absent semantics after reconstruction
    assert not hasattr(restored, "_internal") or restored._internal == "not a param"


def test_from_jsparams_raises_on_non_parameterizable_payload():
    # Use dumps() on a plain dict — it won't carry CLASS/MODULE of a ParameterizableClass
    js = dumps({"a": 1, "b": 2})

    with pytest.raises(TypeError):
        ParameterizableClass.from_jsparams(js)
