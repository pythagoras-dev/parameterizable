from typing import Any

from mixinforge.mixins_and_metaclasses.parameterizable_mixin import ParameterizableMixin
from mixinforge.utility_functions.json_processor import loadjs


class BasicParam(ParameterizableMixin):
    def __init__(self, a: int, b: int = 2, c: str = "x") -> None:
        self.a = a
        self.b = b
        self.c = c

    def get_params(self) -> dict[str, Any]:
        return {"a": self.a, "b": self.b, "c": self.c}


def test_default_essential_is_all_and_auxiliary_is_empty():
    obj = BasicParam(a=1, b=20, c="ok")

    # By default, everything is essential
    assert obj.essential_param_names == {"a", "b", "c"}
    assert obj.get_essential_params() == obj.get_params()

    # Auxiliary is empty by default
    assert obj.auxiliary_param_names == set()
    assert obj.get_auxiliary_params() == {}

    # JSON accessors mirror the dict ones
    assert loadjs(obj.get_essential_jsparams()) == obj.get_params()
    assert loadjs(obj.get_auxiliary_jsparams()) == {}


class SplitParam(BasicParam):
    # Make only a subset essential
    @property
    def essential_param_names(self) -> set[str]:
        return {"a", "b"}


def test_overridden_essential_and_auxiliary_behave_consistently():
    obj = SplitParam(a=10, b=30, c="rest")
    expected_params = {"a": 10, "b": 30, "c": "rest"}

    # Sanity: get_params unchanged from base
    assert obj.get_params() == expected_params

    # Now only a and b are essential
    assert obj.essential_param_names == {"a", "b"}
    assert obj.get_essential_params() == {"a": 10, "b": 30}
    assert loadjs(obj.get_essential_jsparams()) == {"a": 10, "b": 30}

    # Auxiliary contains the rest
    assert obj.auxiliary_param_names == {"c"}
    assert obj.get_auxiliary_params() == {"c": "rest"}
    assert loadjs(obj.get_auxiliary_jsparams()) == {"c": "rest"}
