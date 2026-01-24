"""Tests for transform_instances_inside_composite_object function."""
import pytest
from dataclasses import dataclass
from typing import Optional

from mixinforge.utility_functions.nested_collections_transformer import transform_instances_inside_composite_object


@dataclass(frozen=True)
class Target:
    name: str
    value: int = 0
    nested: Optional['Target'] = None


@dataclass
class Container:
    item: object


def test_transform_simple_list():
    """Transform target objects in a simple list."""
    t1 = Target("a", 1)
    t2 = Target("b", 2)
    data = [t1, "other", t2, 42]

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name.upper(), t.value * 10)
    )

    assert isinstance(result, list)
    assert len(result) == 4
    assert result[0].name == "A" and result[0].value == 10
    assert result[1] == "other"
    assert result[2].name == "B" and result[2].value == 20
    assert result[3] == 42


def test_transform_nested_dict():
    """Transform target objects nested in dict structures."""
    t1 = Target("x", 5)
    t2 = Target("y", 10)
    data = {"first": [t1], "second": {"inner": t2}}

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "_mod", t.value + 100)
    )

    assert result["first"][0].name == "x_mod"
    assert result["first"][0].value == 105
    assert result["second"]["inner"].name == "y_mod"
    assert result["second"]["inner"].value == 110


def test_transform_nested_target_objects():
    """Transform target objects nested inside other target objects."""
    inner = Target("inner", 1)
    outer = Target("outer", 2, nested=inner)

    result = transform_instances_inside_composite_object(
        outer, Target, lambda t: Target(t.name + "!", t.value * 2, t.nested)
    )

    # Outer should be transformed
    assert result.name == "outer!"
    assert result.value == 4
    # Inner nested object should also be transformed
    assert result.nested.name == "inner!"
    assert result.nested.value == 2


def test_no_transformation_when_no_matches():
    """Return original object unchanged when no target instances found."""
    data = [1, 2, {"a": "hello", "b": [3, 4]}]
    original_id = id(data)

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target("new", 999)
    )

    assert result is data
    assert id(result) == original_id


def test_transform_dict_keys():
    """Transform target objects when they are keys in a dictionary."""
    t1 = Target("key1", 1)
    t2 = Target("key2", 2)
    data = {t1: "value1", t2: "value2"}

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "_k", t.value)
    )

    # Check that keys were transformed
    keys = list(result.keys())
    assert len(keys) == 2
    assert all(k.name.endswith("_k") for k in keys)
    # Values should be unchanged
    assert "value1" in result.values()
    assert "value2" in result.values()


def test_transform_dict_values():
    """Transform target objects when they are values in a dictionary."""
    t1 = Target("val1", 10)
    t2 = Target("val2", 20)
    data = {"a": t1, "b": t2}

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name.upper(), t.value // 2)
    )

    assert result["a"].name == "VAL1"
    assert result["a"].value == 5
    assert result["b"].name == "VAL2"
    assert result["b"].value == 10


def test_transform_tuple():
    """Transform preserves tuple type."""
    t1 = Target("t", 7)
    data = (t1, "string", 100)

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target("new_" + t.name, t.value * 3)
    )

    assert isinstance(result, tuple)
    assert len(result) == 3
    assert result[0].name == "new_t"
    assert result[0].value == 21
    assert result[1] == "string"
    assert result[2] == 100


def test_transform_set():
    """Transform works with sets."""
    t1 = Target("s1", 1)
    t2 = Target("s2", 2)
    data = {t1, t2, "other"}

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "_set", t.value)
    )

    assert isinstance(result, set)
    assert len(result) == 3
    target_names = {item.name for item in result if isinstance(item, Target)}
    assert "s1_set" in target_names
    assert "s2_set" in target_names


def test_transform_to_different_type():
    """Transform can change target type to something else."""
    t1 = Target("convert", 42)
    data = [t1, "keep"]

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: f"string_{t.name}_{t.value}"
    )

    assert result[0] == "string_convert_42"
    assert result[1] == "keep"


def test_deduplication_preserves_identity():
    """Same object referenced multiple times uses same transformed instance."""
    t1 = Target("shared", 5)
    data = [t1, t1, {"ref": t1}]

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "_t", t.value)
    )

    # All references should point to the same transformed object
    assert result[0] is result[1]
    assert result[0] is result[2]["ref"]


def test_transform_empty_collection():
    """Transform handles empty collections correctly."""
    data = []

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target("x", 0)
    )

    assert result is data


def test_cycle_handling():
    """Handle cycles gracefully during transformation traversal."""
    c1 = Container(None)
    c2 = Container(c1)
    c1.item = c2  # Cycle: c1 -> c2 -> c1

    # Should transform both containers without raising an error
    result = transform_instances_inside_composite_object(
        c1, Container, lambda c: Container("transformed")
    )

    # Result should be a transformed container
    assert isinstance(result, Container)
    assert result.item == "transformed"


def test_transform_with_none_values():
    """Transform handles None values correctly."""
    t1 = Target("test", 1)
    data = [t1, None, {"key": None, "val": t1}]

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "_n", t.value)
    )

    assert result[0].name == "test_n"
    assert result[1] is None
    assert result[2]["key"] is None
    assert result[2]["val"].name == "test_n"


def test_transform_complex_nested_structure():
    """Transform deeply nested mixed structures."""
    t1 = Target("deep1", 1)
    t2 = Target("deep2", 2)
    t3 = Target("deep3", 3)

    data = {
        "level1": [
            t1,
            {
                "level2": (t2, [{"level3": t3}])
            }
        ]
    }

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(f"T{t.value}", t.value * 100)
    )

    assert result["level1"][0].name == "T1"
    assert result["level1"][0].value == 100
    assert result["level1"][1]["level2"][0].name == "T2"
    assert result["level1"][1]["level2"][0].value == 200
    assert result["level1"][1]["level2"][1][0]["level3"].name == "T3"
    assert result["level1"][1]["level2"][1][0]["level3"].value == 300


def test_transform_preserves_non_target_structure():
    """Transform doesn't alter non-target objects unnecessarily."""
    inner_dict = {"preserved": "value"}
    inner_list = [1, 2, 3]
    data = {"dict": inner_dict, "list": inner_list}

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target("new", 0)
    )

    # Since no Targets found, should return original
    assert result is data
    assert result["dict"] is inner_dict
    assert result["list"] is inner_list


def test_transform_atomic_target_type():
    """Transform works when target_type is an atomic type like str."""
    data = [1, "hello", 2, "world", {"key": "value"}]

    result = transform_instances_inside_composite_object(
        data, str, lambda s: s.upper()
    )

    assert result[0] == 1
    assert result[1] == "HELLO"
    assert result[2] == 2
    assert result[3] == "WORLD"
    # Both dict keys and values are transformed
    assert result[4]["KEY"] == "VALUE"


def test_non_type_classinfo_raises_typeerror():
    """Raise TypeError when classinfo is not a valid type specification."""
    data = [1, 2, 3]

    with pytest.raises(TypeError, match="classinfo"):
        transform_instances_inside_composite_object(data, "not_a_type", lambda x: x)


@pytest.mark.parametrize("invalid_classinfo", [
    None,
    42,
    "str",
    ["list"],  # list is not valid, only tuple
    {"dict": "value"},
    (str, "not_a_type"),  # tuple containing invalid item
    (str, (int, None)),   # nested tuple with invalid item
])
def test_various_invalid_classinfo_raise_typeerror(invalid_classinfo):
    """Various invalid classinfo values should raise TypeError."""
    data = [1, 2, 3]

    with pytest.raises(TypeError):
        transform_instances_inside_composite_object(data, invalid_classinfo, lambda x: x)


def test_non_callable_transform_fn_raises_typeerror():
    """Raise TypeError when transform_fn is not callable."""
    data = [Target("a", 1)]

    with pytest.raises(TypeError, match="transform_fn"):
        transform_instances_inside_composite_object(data, Target, "not_callable")


@pytest.mark.parametrize("invalid_fn", [
    None,
    42,
    "string",
    [1, 2, 3],
    {"key": "value"},
])
def test_various_non_callable_transform_fn_raise_typeerror(invalid_fn):
    """Various non-callable values should raise TypeError."""
    data = [Target("a", 1)]

    with pytest.raises(TypeError):
        transform_instances_inside_composite_object(data, Target, invalid_fn)


def test_transform_applies_to_root_object():
    """Transform works when root object itself is target type."""
    root = Target("root", 99)

    result = transform_instances_inside_composite_object(
        root, Target, lambda t: Target("transformed_root", t.value + 1)
    )

    assert result.name == "transformed_root"
    assert result.value == 100


def test_transform_with_multiple_types_in_hierarchy():
    """Transform only affects specified type in mixed hierarchy."""
    t1 = Target("t1", 1)
    c1 = Container(t1)
    data = [c1, Target("t2", 2)]

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "_x", 0)
    )

    # Container should be unchanged, but Target inside it should transform
    assert isinstance(result[0], Container)
    assert result[0].item.name == "t1_x"
    assert result[1].name == "t2_x"


def test_cycle_preservation_in_list():
    """Verify cycles are preserved in transformed structures."""
    # Create a cycle: list -> inner_list -> list
    inner_list = [Target("inner", 1)]
    outer_list = [Target("outer", 2), inner_list]
    inner_list.append(outer_list)

    result = transform_instances_inside_composite_object(
        outer_list, Target, lambda t: Target(t.name + "_transformed", t.value * 10)
    )

    # Check transformations were applied
    assert result[0].name == "outer_transformed"
    assert result[0].value == 20

    # Check cycle is preserved
    assert result[1][0].name == "inner_transformed"
    assert result[1][0].value == 10
    # The cycle should be preserved: result[1][1] should be result
    assert result[1][1] is result


def test_cycle_preservation_with_shared_structure():
    """DAG (directed acyclic graph) structure preserved after transformation."""
    shared_target = Target("shared", 99)
    container1 = Container(shared_target)
    container2 = Container(shared_target)
    data = [container1, container2]

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target("new_" + t.name, t.value + 1)
    )

    # Both containers should reference the SAME transformed target
    assert result[0].item is result[1].item
    assert result[0].item.name == "new_shared"
    assert result[0].item.value == 100


def test_transform_preserves_object_cycles():
    """Transform detects and processes cycles correctly."""
    c1 = Container(None)
    c2 = Container(c1)
    c1.item = c2  # Cycle: c1 -> c2 -> c1

    # Transform with a simple modification
    result = transform_instances_inside_composite_object(
        c1, Container, lambda c: Container("transformed")
    )

    # The transformation should complete without error (cycle handled)
    assert isinstance(result, Container)
    assert result.item == "transformed"


def test_cycle_with_dict_key_transformation():
    """Dict with target objects as keys in cyclic structure."""
    t1 = Target("key1", 1)
    d = {t1: []}
    d[t1].append(d)  # Cycle: dict value contains the dict itself

    result = transform_instances_inside_composite_object(
        d, Target, lambda t: Target(t.name + "_new", t.value)
    )

    # Verify transformation applied to key
    keys = list(result.keys())
    assert len(keys) == 1
    assert keys[0].name == "key1_new"
    assert keys[0].value == 1

    # Verify cycle preserved: the list in the value should contain the dict
    assert len(result[keys[0]]) == 1
    assert result[keys[0]][0] is result


def test_multiple_independent_cycles():
    """Structure with multiple separate cycles."""
    # Create first cycle
    cycle1_a = [Target("c1a", 1)]
    cycle1_b = [Target("c1b", 2), cycle1_a]
    cycle1_a.append(cycle1_b)

    # Create second cycle
    cycle2_a = [Target("c2a", 3)]
    cycle2_b = [Target("c2b", 4), cycle2_a]
    cycle2_a.append(cycle2_b)

    data = [cycle1_a, cycle2_a]
    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "_x", t.value * 10)
    )

    # Verify transformations applied
    assert result[0][0].name == "c1a_x"
    assert result[0][0].value == 10
    assert result[0][1][0].name == "c1b_x"
    assert result[0][1][0].value == 20

    assert result[1][0].name == "c2a_x"
    assert result[1][0].value == 30
    assert result[1][1][0].name == "c2b_x"
    assert result[1][1][0].value == 40

    # Verify both cycles preserved
    assert result[0][1][1] is result[0]
    assert result[1][1][1] is result[1]

    # Verify cycles are independent (don't point to each other)
    assert result[0][1][1] is not result[1]
    assert result[1][1][1] is not result[0]


def test_deeply_nested_with_cycle():
    """Very deep structure with cycle at the bottom."""
    deep = [[[[[Target("deep", 1)]]]]]
    deep[0][0][0][0].append(deep)  # Cycle back to root

    result = transform_instances_inside_composite_object(
        deep, Target, lambda t: Target(t.name + "!", t.value)
    )

    # Verify transformation at deep level
    assert result[0][0][0][0][0].name == "deep!"
    assert result[0][0][0][0][0].value == 1

    # Verify cycle preserved
    assert result[0][0][0][0][1] is result


def test_cycle_in_mixed_collection_types():
    """Cycle involving different collection types (list, dict, tuple)."""
    t1 = Target("t1", 1)
    lst = [t1]
    dct = {"key": Target("t2", 2), "list": lst}
    tpl = (Target("t3", 3), dct)
    lst.append(tpl)  # Cycle: lst -> tpl -> dct -> lst

    result = transform_instances_inside_composite_object(
        lst, Target, lambda t: Target(t.name + "_mod", t.value + 100)
    )

    # Verify transformations
    assert result[0].name == "t1_mod"
    assert result[0].value == 101

    # Navigate through cycle
    assert result[1][0].name == "t3_mod"
    assert result[1][0].value == 103

    assert result[1][1]["key"].name == "t2_mod"
    assert result[1][1]["key"].value == 102

    # Verify cycle: result[1][1]["list"] should be result
    assert result[1][1]["list"] is result


# ==============================================================================
# Tests for deep_transformation parameter
# ==============================================================================

def test_shallow_transformation_stops_at_nested_target():
    """With deep_transformation=False, nested targets inside transformed instances are not transformed."""
    inner = Target("inner", 1)
    outer = Target("outer", 2, nested=inner)

    result = transform_instances_inside_composite_object(
        outer, Target, lambda t: Target(t.name + "!", t.value * 2, t.nested),
        deep_transformation=False
    )

    assert result.name == "outer!"
    assert result.value == 4
    # Inner should NOT be transformed
    assert result.nested.name == "inner"
    assert result.nested.value == 1


def test_shallow_transformation_traverses_non_target_containers():
    """With deep_transformation=False, targets in non-target containers are still found and transformed."""
    t1 = Target("first", 1)
    t2 = Target("second", 2)
    data = {"a": t1, "b": [t2]}

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "!", t.value * 10),
        deep_transformation=False
    )

    assert result["a"].name == "first!"
    assert result["a"].value == 10
    assert result["b"][0].name == "second!"
    assert result["b"][0].value == 20


def test_shallow_transformation_multilevel_nesting():
    """With deep_transformation=False, only the outermost target is transformed."""
    level3 = Target("level3", 3)
    level2 = Target("level2", 2, nested=level3)
    level1 = Target("level1", 1, nested=level2)

    result = transform_instances_inside_composite_object(
        level1, Target, lambda t: Target(t.name + "!", t.value * 10, t.nested),
        deep_transformation=False
    )

    assert result.name == "level1!"
    assert result.value == 10
    # level2 and level3 should NOT be transformed
    assert result.nested.name == "level2"
    assert result.nested.value == 2
    assert result.nested.nested.name == "level3"
    assert result.nested.nested.value == 3


def test_shallow_transformation_sibling_targets_in_container():
    """With deep_transformation=False, sibling targets in a container are all transformed."""
    inner1 = Target("inner1", 1)
    inner2 = Target("inner2", 2)
    outer1 = Target("outer1", 10, nested=inner1)
    outer2 = Target("outer2", 20, nested=inner2)
    data = [outer1, outer2]

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "!", t.value * 2, t.nested),
        deep_transformation=False
    )

    # Both outer targets are transformed (they are siblings in the list)
    assert result[0].name == "outer1!"
    assert result[1].name == "outer2!"
    # But their nested children are NOT transformed
    assert result[0].nested.name == "inner1"
    assert result[1].nested.name == "inner2"


def test_shallow_transformation_shared_nested_target():
    """With deep_transformation=False, shared nested targets are not transformed."""
    shared = Target("shared", 99)
    outer1 = Target("outer1", 1, nested=shared)
    outer2 = Target("outer2", 2, nested=shared)
    data = [outer1, outer2]

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "!", t.value, t.nested),
        deep_transformation=False
    )

    # Both outers transformed
    assert result[0].name == "outer1!"
    assert result[1].name == "outer2!"
    # Shared nested target NOT transformed
    assert result[0].nested.name == "shared"
    assert result[1].nested.name == "shared"
    # And both still reference the same (untransformed) shared object
    assert result[0].nested is result[1].nested


def test_deep_transformation_default_is_true():
    """Verify default behavior with no deep_transformation argument matches deep_transformation=True."""
    inner = Target("inner", 1)
    outer = Target("outer", 2, nested=inner)

    result_default = transform_instances_inside_composite_object(
        outer, Target, lambda t: Target(t.name + "!", t.value * 2, t.nested)
    )

    # Both should be transformed (default deep_transformation=True)
    assert result_default.name == "outer!"
    assert result_default.nested.name == "inner!"


def test_shallow_transformation_mixed_containers():
    """With deep_transformation=False, traversal continues through all non-target container types."""
    nested_target = Target("nested", 1)
    outer_target = Target("outer", 2, nested=nested_target)
    data = {"dict": [{"inner_dict": (outer_target,)}]}

    result = transform_instances_inside_composite_object(
        data, Target, lambda t: Target(t.name + "!", t.value * 10, t.nested),
        deep_transformation=False
    )

    # Outer target found and transformed
    assert result["dict"][0]["inner_dict"][0].name == "outer!"
    # Nested target NOT transformed
    assert result["dict"][0]["inner_dict"][0].nested.name == "nested"


# ==============================================================================
# Tests for tuple of types and union types (classinfo parameter)
# ==============================================================================

def test_transform_with_tuple_of_types():
    """Transform instances matching any type in a tuple."""
    t1 = Target("target1", 1)
    data = [t1, "hello", 42, 3.14]

    def transform(x):
        if isinstance(x, Target):
            return Target(x.name + "!", x.value * 10)
        if isinstance(x, str):
            return x.upper()
        return x

    result = transform_instances_inside_composite_object(data, (Target, str), transform)

    # Note: The Target's name is also a string, so it gets transformed too (deep transformation)
    # First the Target is transformed (name becomes "target1!"), then the name string
    # inside the new Target is also transformed (becomes "TARGET1!")
    assert result[0].name == "TARGET1!"
    assert result[0].value == 10
    assert result[1] == "HELLO"
    assert result[2] == 42  # unchanged
    assert result[3] == 3.14  # unchanged


def test_transform_with_nested_tuple_of_types():
    """Transform instances with nested tuple of types."""
    data = ["hello", 42, 3.14]

    result = transform_instances_inside_composite_object(
        data,
        (str, (int, float)),  # nested tuple
        lambda x: str(x) + "_transformed"
    )

    assert result[0] == "hello_transformed"
    assert result[1] == "42_transformed"
    assert result[2] == "3.14_transformed"


def test_transform_with_union_type():
    """Transform instances using union type syntax (Python 3.10+)."""
    data = ["hello", 42, 3.14]

    result = transform_instances_inside_composite_object(
        data,
        str | int,  # union type
        lambda x: f"[{x}]"
    )

    assert result[0] == "[hello]"
    assert result[1] == "[42]"
    assert result[2] == 3.14  # float unchanged


def test_transform_with_empty_tuple():
    """Empty tuple of types transforms nothing, returns original."""
    data = [1, "hello", Target("t", 1)]

    result = transform_instances_inside_composite_object(data, (), lambda x: "changed")

    assert result is data  # no matches, original returned


def test_transform_with_single_type_in_tuple():
    """Single type wrapped in tuple works like single type."""
    t1 = Target("target1", 1)
    data = [t1, "hello", 42]

    result = transform_instances_inside_composite_object(
        data,
        (Target,),
        lambda t: Target(t.name + "!", t.value)
    )

    assert result[0].name == "target1!"
    assert result[1] == "hello"
    assert result[2] == 42


def test_transform_multiple_types_in_nested_structure():
    """Transform multiple types in deeply nested structure."""
    t1 = Target("t1", 1)
    data = {
        "targets": [t1],
        "strings": ["a", "b"],
        "numbers": [1, 2, 3],
        "nested": {"inner": Target("inner", 2)}
    }

    def transform(x):
        if isinstance(x, Target):
            return Target(x.name.upper(), x.value * 100)
        if isinstance(x, str):
            return x + "!"
        return x

    result = transform_instances_inside_composite_object(data, (Target, str), transform)

    # Note: dict keys are also strings and get transformed
    assert result["targets!"][0].name == "T1!"  # name is a string, gets transformed too
    assert result["strings!"] == ["a!", "b!"]   # strings in list transformed once
    assert result["numbers!"] == [1, 2, 3]
    assert result["nested!"]["inner!"].name == "INNER!"
