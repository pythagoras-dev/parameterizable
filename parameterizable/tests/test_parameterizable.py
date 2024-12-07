from parameterizable import *
from parameterizable.parameterizable import _known_parameterizable_classes
from parameterizable.parameterizable import _smoketest_parameterizable_class
from abc import *

class GoodPameterizable(ABC, ParameterizableClass):
    def __init__(self, a: int = 10, b: str = "hello", c=int):
        ParameterizableClass.__init__(self)
        self.a = a
        self.b = b
        self.c = c

    def get_params(self) -> dict[str, Any]:
        params = dict(a=self.a, b=self.b, c=self.c)
        return params


def test_good_class():
    _known_parameterizable_classes.clear()
    assert is_parameterizable(GoodPameterizable)
    assert _smoketest_parameterizable_class(GoodPameterizable)
    assert len(_known_parameterizable_classes) == 1
    register_parameterizable_class(GoodPameterizable)
    assert len(_known_parameterizable_classes) == 1
    obj = GoodPameterizable()
    obj.a = -12345
    obj.b = "Hi!"
    obj.c = str
    params = obj.__get_portable_params__()
    assert params["a"] == -12345
    assert params["b"] == "Hi!"
    assert type(params["c"]) == dict
    obj2 = get_object_from_portable_params(params)
    assert obj2.a == -12345
    assert obj2.b == "Hi!"
    assert obj2.c == str
    _known_parameterizable_classes.clear()

class EvenBetterOne(GoodPameterizable):
    def __init__(self, a: int = 10, b: str = "hello", c=int, d: float = 3.14):
        GoodPameterizable.__init__(self, a, b, c)
        self.d = d

    def get_params(self) -> dict[str, Any]:
        params = super().get_params()
        params["d"] = self.d
        return params

def test_even_better_one():
    _known_parameterizable_classes.clear()
    x = EvenBetterOne()
    assert len(_known_parameterizable_classes) == 1
    _known_parameterizable_classes.clear()


class EmptyClass:
    pass

def test_empty_class():
    assert not is_parameterizable(EmptyClass)







