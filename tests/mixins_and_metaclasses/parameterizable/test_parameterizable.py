import json
from typing import Any


from mixinforge.mixins_and_metaclasses.parameterizable_mixin import ParameterizableMixin
from mixinforge.utility_functions.json_processor import loadjs


class MyParam(ParameterizableMixin):
    def __init__(
        self,
        a: int,
        b: int = 2,
        c: str = "x",
        d: Any = None,
        *,
        e: int = 5,
        f: int = 7,
        **kwargs,
    ) -> None:
        # store everything so that get_params can see it
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f
        # an auxiliary-only parameter (not present among defaults)
        self.verbose = kwargs.get("verbose", False)

    def get_params(self) -> dict[str, Any]:
        return {
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
            "e": self.e,
            "f": self.f,
            "verbose": self.verbose,
        }


def test_base_class_defaults_and_jsparams_are_empty():
    # Base class returns empty params dict
    base = ParameterizableMixin()
    assert base.get_params() == {}

    js = base.get_jsparams()
    assert isinstance(js, str)
    assert loadjs(js) == {}


def test_get_default_params_collects_init_defaults_and_sorts_keys():
    # Required-only param 'a' must NOT be in defaults
    expected_defaults = {"b": 2, "c": "x", "d": None, "e": 5, "f": 7}

    got = MyParam.get_default_params()
    # Ensure keys are sorted lexicographically
    assert list(got.keys()) == sorted(expected_defaults.keys())
    assert got == expected_defaults

    # JSON variant round-trips to the same mapping
    js = MyParam.get_default_jsparams()
    assert loadjs(js) == expected_defaults


def test_instance_jsparams_is_dump_of_params_dict():
    obj = MyParam(a=10, b=20, c="ok", e=50, f=70)

    params = obj.get_params()
    js = obj.get_jsparams()

    # get_jsparams returns dumpjs of a plain dict → loadjs returns the same dict
    assert loadjs(js) == params

    # And dumpjs/loadjs are indeed JSON – the payload is a JSON string
    # Validate it parses with the stdlib json loader too
    json.loads(js)


def test_repr_includes_class_name_and_params():
    # Base class (no params)
    base = ParameterizableMixin()
    assert repr(base) == "ParameterizableMixin({})"

    # Subclass (with params)
    obj = MyParam(a=1)
    # The repr should look like "MyParam({'a': 1, 'b': 2, ...})"
    r = repr(obj)
    assert r.startswith("MyParam(")
    assert "'a': 1" in r
    assert "'b': 2" in r
    assert "'verbose': False" in r
