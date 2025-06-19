from src.parameterizable.parameterizable import *
from src.parameterizable.parameterizable import _known_parameterizable_classes
from src.parameterizable.parameterizable import CLASSNAME_PARAM_KEY

# Import the test class from test_basic to reuse it
from tests.demo_types import GoodPameterizable


def test_nested_parameterizable_objects():
    _known_parameterizable_classes.clear()

    class NestedContainer(ParameterizableClass):
        def __init__(self, nested_obj=None):
            super().__init__()
            self.nested_obj = nested_obj if nested_obj else GoodPameterizable()

        def get_params(self):
            return {"nested_obj": self.nested_obj}

    # Create a container with a nested parameterizable object
    inner_obj = GoodPameterizable(a=100, b="nested", c=float)
    container = NestedContainer(inner_obj)

    # Convert to portable params
    portable_params = container.get_portable_params()

    # Check that the nested object is properly converted
    assert CLASSNAME_PARAM_KEY in portable_params["nested_obj"]
    assert portable_params["nested_obj"][CLASSNAME_PARAM_KEY] == "GoodPameterizable"
    assert portable_params["nested_obj"]["a"] == 100
    assert portable_params["nested_obj"]["b"] == "nested"

    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)

    # Check that the nested object is properly reconstructed
    assert isinstance(reconstructed.nested_obj, GoodPameterizable)
    assert reconstructed.nested_obj.a == 100
    assert reconstructed.nested_obj.b == "nested"
    assert reconstructed.nested_obj.c == float

    _known_parameterizable_classes.clear()


def test_collections_with_parameterizable_objects():
    _known_parameterizable_classes.clear()

    class CollectionContainer(ParameterizableClass):
        def __init__(self, obj_list=None, obj_dict=None):
            super().__init__()
            self.obj_list = obj_list if obj_list is not None else []
            self.obj_dict = obj_dict if obj_dict is not None else {}

        def get_params(self):
            return {"obj_list": self.obj_list, "obj_dict": self.obj_dict}

    # Create parameterizable objects to put in collections
    obj1 = GoodPameterizable(a=1, b="one", c=str)
    obj2 = GoodPameterizable(a=2, b="two", c=int)

    # Create a container with collections containing parameterizable objects
    container = CollectionContainer(
        obj_list=[obj1, obj2, "string", 42],
        obj_dict={"obj1": obj1, "obj2": obj2, "str": "string", "num": 42}
    )

    # Convert to portable params
    portable_params = container.get_portable_params()

    # Check that the collections are properly converted
    assert isinstance(portable_params["obj_list"], list)
    assert len(portable_params["obj_list"]) == 4
    assert CLASSNAME_PARAM_KEY in portable_params["obj_list"][0]
    assert CLASSNAME_PARAM_KEY in portable_params["obj_list"][1]
    assert portable_params["obj_list"][2] == "string"
    assert portable_params["obj_list"][3] == 42

    assert isinstance(portable_params["obj_dict"], dict)
    assert len(portable_params["obj_dict"]) == 4
    assert CLASSNAME_PARAM_KEY in portable_params["obj_dict"]["obj1"]
    assert CLASSNAME_PARAM_KEY in portable_params["obj_dict"]["obj2"]
    assert portable_params["obj_dict"]["str"] == "string"
    assert portable_params["obj_dict"]["num"] == 42

    # Reconstruct from portable params
    reconstructed = get_object_from_portable_params(portable_params)

    # Check that the collections are properly reconstructed
    assert isinstance(reconstructed.obj_list, list)
    assert len(reconstructed.obj_list) == 4
    assert isinstance(reconstructed.obj_list[0], GoodPameterizable)
    assert isinstance(reconstructed.obj_list[1], GoodPameterizable)
    assert reconstructed.obj_list[2] == "string"
    assert reconstructed.obj_list[3] == 42

    assert isinstance(reconstructed.obj_dict, dict)
    assert len(reconstructed.obj_dict) == 4
    assert isinstance(reconstructed.obj_dict["obj1"], GoodPameterizable)
    assert isinstance(reconstructed.obj_dict["obj2"], GoodPameterizable)
    assert reconstructed.obj_dict["str"] == "string"
    assert reconstructed.obj_dict["num"] == 42

    # Check specific values in the reconstructed objects
    assert reconstructed.obj_list[0].a == 1
    assert reconstructed.obj_list[0].b == "one"
    assert reconstructed.obj_list[0].c == str
    assert reconstructed.obj_list[1].a == 2
    assert reconstructed.obj_list[1].b == "two"
    assert reconstructed.obj_list[1].c == int

    _known_parameterizable_classes.clear()