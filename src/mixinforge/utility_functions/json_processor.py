"""JSON-compatible serialization helpers for complex Python objects.

This module provides functions to convert rich Python data structures into a
JSON-serializable representation and back. It supports primitive types as well
as containers (list, tuple, set, dict), Enums, and certain custom objects.

The serialized form is a pure-JSON structure containing only dicts, lists,
strings, numbers, booleans, and null. Special container and object types are
encoded using internal marker keys.
"""

import importlib
import json
import types
from enum import Enum
from typing import Any, Final, Mapping, NewType

from ..utility_functions.dict_sorter import sort_dict_by_keys

JsonSerializedObject = NewType("JsonSerializedObject", str)

_UNSUPPORTED_TYPES: Final[tuple[type,...]] = (
    types.ModuleType,
    types.FunctionType,
    types.LambdaType,
    types.BuiltinFunctionType,
    types.MethodType,
    types.CodeType,
    type,
)

class _Markers:
    """Internal keys used to tag non-JSON-native constructs.

    The serializer uses these markers inside dictionaries to encode special
    types and object metadata while still producing a JSON-compatible structure.

    Attributes:
        DICT: Marker for dictionaries to ensure all keys are strings and values
            are JSON-serializable.
        TUPLE: Marker key for tuple values. The value is a list of items.
        SET: Marker key for set values. The value is a list of items.
        ENUM: Marker key for Enum members. The value is the member name.
        CLASS: Name of the object's class used during reconstruction.
        MODULE: Name of the module where the object's class is defined.
        PARAMS: Serialized mapping of constructor parameters for get_params-
            based reconstruction.
        STATE: Serialized state for __getstate__/__setstate__-based
            reconstruction.
    """

    DICT = "..dict.."
    TUPLE = "..tuple.."
    SET = "..set.."
    CLASS = "..class.."
    MODULE = "..module.."
    PARAMS = "..params.."
    STATE = "..state.."
    ENUM = "..enum.."


def _to_serializable_dict(x: Any, seen: set[int] | None = None) -> Any:
    """Convert a Python object into a JSON-serializable structure.

    The transformation is recursive and supports primitives, lists, tuples,
    sets, and dicts. Certain custom objects are supported either through
    a get_params method or the pickle protocol __getstate__.

    Args:
        x: The object to convert.
        seen:  A set of visited object ids for cycle detection.

    Returns:
        A structure composed only of JSON-compatible types (dict, list, str,
        int, float, bool, None), potentially enhanced with internal marker
        keys to represent tuples, sets, and reconstructable objects.

    Raises:
        TypeError: If x (or any nested value) contains an unsupported type.

    Examples:
        - Tuples and sets are encoded with markers:

          >>> _to_serializable_dict((1, 2))
          {'..tuple..': [1, 2]}
          >>> _to_serializable_dict({1, 2})
          {'..set..': [1, 2]}
    """

    if isinstance(x,(int, float, bool, str, type(None))):
        return x
    elif isinstance(x, _UNSUPPORTED_TYPES):
        raise TypeError(f"Unsupported type: {type(x).__name__}")

    if seen is None:
        seen = set()

    obj_id = id(x)
    if obj_id in seen:
        raise RecursionError(
            f"Cyclic reference detected while serializing object of type {type(x).__name__}")
    seen.add(obj_id)

    try:
        if hasattr(x, "get_params"):
            result = _process_state(x.get_params(), x, _Markers.PARAMS, seen)
        elif isinstance(x, list):
            result = [_to_serializable_dict(i, seen) for i in x]
        elif isinstance(x, tuple):
            result = {_Markers.TUPLE: [_to_serializable_dict(i, seen) for i in x]}
        elif isinstance(x, set):
            result = {_Markers.SET: [_to_serializable_dict(i, seen) for i in x]}
        elif isinstance(x, dict):
            result = {_Markers.DICT: { k: _to_serializable_dict(v, seen)
                for k, v in x.items()}}
        elif isinstance(x, Enum):
            result = {_Markers.ENUM: x.name,
                _Markers.CLASS: x.__class__.__qualname__,
                _Markers.MODULE: x.__class__.__module__,}
        elif hasattr(x, "__getstate__"):
            result = _process_state(x.__getstate__(), x, _Markers.STATE, seen)
        elif hasattr(x.__class__, "__slots__"):
            # For slotted objects, create a pickle-style state tuple
            slots = _get_all_slots(type(x))
            # Raises AttributeError if a slot is uninitialized
            slot_state = tuple(getattr(x, name) for name in slots)

            if hasattr(x, "__dict__"):
                # Hybrid object with slots and dict
                final_state = (slot_state, x.__dict__)
            else:
                # Slots-only object: use a (slots, None) tuple for consistency
                # in the reconstruction logic.
                final_state = (slot_state, None)
            result = _process_state(final_state, x, _Markers.STATE, seen)
        elif hasattr(x, "__dict__"):
            result = _process_state(x.__dict__, x, _Markers.STATE, seen)
        else:
            raise TypeError(f"Unsupported type: {type(x).__name__}")
    finally:
        seen.remove(obj_id)
    return result


def _process_state(state: Any, obj: Any, marker: str, seen: set[int]) -> dict:
    """Wrap object identity and state into a marker-bearing mapping.

    Produces a dictionary containing the object's class and module names along
    with the provided state under the specified marker (e.g., PARAMS or
    STATE). The state is recursively converted to JSON-serializable types.

    Args:
        state: The object's state, e.g. from __getstate__.
        obj: The object being serialized (used to extract class/module names).
        marker: Which marker to use for the state payload.
        seen: A set of visited object ids for cycle detection.

    Returns:
        A dictionary suitable for JSON encoding that can be used by
        _recreate_object to rebuild the instance.
    """

    return {_Markers.CLASS: obj.__class__.__qualname__,
        _Markers.MODULE: obj.__class__.__module__,
        marker: _to_serializable_dict(state, seen)}


def _get_all_slots(cls: type) -> list[str]:
    """Collect all slot names from a class hierarchy, excluding special ones.

    Args:
        cls: The class to inspect for __slots__.

    Returns:
        List of slot names in MRO order, excluding __dict__ and __weakref__.
    """
    slots_to_fill = []
    # Traverse in reverse MRO to maintain parent-to-child slot order
    for base_cls in reversed(cls.__mro__):
        base_slots = getattr(base_cls, "__slots__", [])
        if isinstance(base_slots, str):
            base_slots = [base_slots]
        for slot_name in base_slots:
            if slot_name in ("__dict__", "__weakref__"):
                continue
            slots_to_fill.append(slot_name)
    return slots_to_fill


def _recreate_object(x: Mapping[str,Any]) -> Any:
    """Recreate an object instance from its serialized metadata.

    The input mapping must include MODULE and CLASS markers and either
    PARAMS (constructor parameters), STATE (instance state), or ENUM
    (Enum member name).

    Args:
        x: Marker-bearing mapping produced by _to_serializable_dict for
           custom objects.

    Returns:
        A new instance of the referenced class reconstructed from parameters,
        state, or Enum membership.

    Raises:
        TypeError: If the mapping does not contain sufficient information to
            reconstruct the object.
        ImportError: If the target module cannot be imported. (Surfaced via the
            underlying import mechanism.)
        AttributeError: If the class does not exist in the target module.
    """
    if not isinstance(x, Mapping):
        raise TypeError(f"Object metadata must be a mapping, "
                        f"got: {type(x).__name__}")
    if _Markers.MODULE not in x or _Markers.CLASS not in x:
        raise TypeError("Object metadata missing required markers "
                        "MODULE and CLASS")

    module_name = x[_Markers.MODULE]
    class_name = x[_Markers.CLASS]
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Could not import {class_name} from {module_name}"
                          ) from e

    match x:
        case {_Markers.PARAMS: params_json}:
            return cls(**_from_serializable_dict(params_json))
        case {_Markers.ENUM: member_name}:
            if not issubclass(cls, Enum):
                raise TypeError(f"Class {class_name} is not an Enum")
            return cls[member_name]
        case {_Markers.STATE: state_json}:
            state = _from_serializable_dict(state_json)
            obj = cls.__new__(cls)
            if hasattr(obj, "__setstate__"):
                obj.__setstate__(state)
            elif isinstance(state, tuple):
                # Handle tuple state from __getstate__ for slotted classes
                slots_to_fill = _get_all_slots(cls)

                # Support multiple tuple state formats:
                # 1) (slot_values_seq, dict_values) where slot_values_seq is a sequence of values
                # 2) (dict_values, slot_mapping) as produced by CPython's built-in __getstate__ for slotted classes
                # 3) A plain tuple of slot values
                slot_values_seq = None
                slot_mapping = None
                dict_values = None

                if len(state) == 2:
                    a, b = state
                    if isinstance(a, dict) and isinstance(b, dict):
                        # CPython default: (dict_values, slot_mapping)
                        dict_values = a
                        slot_mapping = b
                    elif isinstance(a, (list, tuple)) and (b is None or isinstance(b, dict)):
                        # Our encoder format: (slot_values_seq, dict_values)
                        slot_values_seq = list(a)
                        dict_values = b
                    elif isinstance(a, dict) and isinstance(b, (list, tuple)):
                        # Be tolerant if components are swapped
                        dict_values = a
                        slot_values_seq = list(b)
                    elif a is None and isinstance(b, dict):
                        # No slots, only dict
                        dict_values = b
                    else:
                        # Fallback: treat entire state as slot values
                        slot_values_seq = list(state)
                else:
                    # Otherwise, state is just a tuple of slot values
                    slot_values_seq = list(state)

                # Apply slots
                if slot_mapping is not None:
                    for name, value in slot_mapping.items():
                        setattr(obj, name, value)
                elif slot_values_seq is not None and len(slot_values_seq) > 0:
                    if len(slot_values_seq) != len(slots_to_fill):
                        raise TypeError(
                            f"Tuple state length {len(slot_values_seq)} does not match "
                            f"slots length {len(slots_to_fill)} for class {cls.__name__}")
                    for value, name in zip(slot_values_seq, slots_to_fill):
                        setattr(obj, name, value)

                # Apply dict attributes, if any
                if dict_values:
                    for k, v in dict_values.items():
                        setattr(obj, k, v)

            else: # Fallback reconstruction
                for k, v in state.items():
                    setattr(obj, k, v)
            return obj
        case _:
            raise TypeError("Unable to recreate object from provided data")


def _from_serializable_dict(x: Any) -> Any:
    """Inverse of _to_serializable_dict.

    Recursively convert a JSON-compatible structure that may contain internal
    markers back into native Python types and reconstruct supported custom
    objects.

    Args:
        x: The JSON-loaded Python structure to convert.

    Returns:
        The reconstructed Python object graph.

    Raises:
        TypeError: If an unsupported structure is encountered.
    """
    match x:
        case None | bool() | int() | float() | str():
            return x
        case list():
            return [_from_serializable_dict(i) for i in x]
        case {_Markers.TUPLE: val}:
            if not len(x) == 1:
                raise TypeError("TUPLE marker must be the only key")
            if not isinstance(val, list):
                raise TypeError("TUPLE marker must map to a list")
            return tuple(_from_serializable_dict(i) for i in val)
        case {_Markers.SET: val}:
            if not len(x) == 1:
                raise TypeError("SET marker must be the only key")
            if not isinstance(val, list):
                raise TypeError("SET marker must map to a list")
            return set(_from_serializable_dict(i) for i in val)
        case {_Markers.DICT: val}:
            if not len(x) == 1:
                raise TypeError("DICT marker must be the only key")
            if not isinstance(val, dict):
                raise TypeError("DICT marker must map to a dict")
            return {k: _from_serializable_dict(v) for k, v in val.items()}
        case {_Markers.MODULE: _, **__} | {_Markers.CLASS: _, **__} as d:
            return _recreate_object(d)
        case _:
            raise TypeError(f"Unsupported type: {type(x).__name__}")


def dumpjs(obj: Any, **kwargs) -> JsonSerializedObject:
    """Dump an object to a JSON string using the custom serialization rules.

    Args:
        obj: The object to serialize.
        **kwargs: Additional keyword arguments forwarded to
            json.dumps (e.g., indent=2, sort_keys=True).

    Returns:
        The JSON string representing the object.
    """
    return json.dumps(_to_serializable_dict(obj), **kwargs)


def loadjs(s: JsonSerializedObject, **kwargs) -> Any:
    """Load an object from a JSON string produced by dumpjs.

    Args:
        s: The JSON string to parse.
        **kwargs: Additional keyword arguments forwarded to
            json.loads (object_hook is not allowed here).

    Returns:
        The Python object reconstructed from the JSON string.

    Raises:
        TypeError: If s is not a string.
        ValueError: If object_hook is provided in kwargs.
    """
    if not isinstance(s, str):
        raise TypeError(f"s must be a string, got {type(s).__name__}")
    if "object_hook" in kwargs:
        raise ValueError("object_hook cannot be used with mixinforge.loadjs()")
    return _from_serializable_dict(json.loads(s, **kwargs))


def _extract_params_dict(container: dict) -> dict:
    """Extract the parameter dictionary from a serialized container.

    Args:
        container: A dictionary containing serialized parameters.

    Returns:
        The parameter dictionary extracted from PARAMS->DICT or top-level DICT.

    Raises:
        KeyError: If the expected DICT structure is not found.
    """
    def pick(block: Any) -> dict | None:
        if isinstance(block, dict):
            candidate = block.get(_Markers.DICT)
            if isinstance(candidate, dict):
                return candidate
        return None

    if _Markers.PARAMS in container:
        candidate = pick(container[_Markers.PARAMS])
        if candidate is None:
            raise KeyError(f"Invalid structure: {_Markers.PARAMS} missing {_Markers.DICT} mapping")
        return candidate

    candidate = pick(container)
    if candidate is None:
        raise KeyError(f"Invalid structure: missing {_Markers.DICT} mapping in JSON object")
    return candidate


def update_jsparams(jsparams: JsonSerializedObject, **kwargs) -> JsonSerializedObject:
    """Update constructor parameters inside a serialized JSON blob.

    This helper takes a JSON string produced by dumpjs for an object that
    was serialized via its get_params method and returns a new JSON string
    with the provided parameters updated or added under the internal
    PARAMS -> DICT mapping.

    Args:
        jsparams: The JSON string returned by dumpjs.
        **kwargs: Key-value pairs to merge into the serialized parameters.
            Existing keys are overwritten; new keys are added.

    Returns:
        A new JSON string with updated parameters.

    Raises:
        TypeError: If jsparams is not a string.
        KeyError: If jsparams does not contain the expected
            PARAMS -> DICT structure (i.e., the input is not a serialized
            mixinforge object).
    """
    if not isinstance(jsparams, str):
        raise TypeError(f"jsparams must be a string, got {type(jsparams).__name__}")
    params = json.loads(jsparams)

    if not isinstance(params, dict):
        raise KeyError("Invalid structure: JSON root must be a dictionary")

    target_dict = _extract_params_dict(params)

    for k, v in kwargs.items():
        target_dict[k] = _to_serializable_dict(v)

    params = sort_dict_by_keys(params)
    params_json = json.dumps(params)
    return JsonSerializedObject(params_json)


def access_jsparams(jsparams: JsonSerializedObject, *args: str) -> dict[str, Any]:
    """Access selected constructor parameters from a serialized JSON blob.

     Args:
         jsparams: The JSON string produced by dumpjs.
         *args: Parameter names to extract from the internal PARAMS -> DICT
             mapping.

     Returns:
         A mapping of requested parameter names to their deserialized
         values. The values are reconstructed Python objects (e.g., tuples, sets,
         dicts) rather than the raw internal JSON representation.

     Raises:
         TypeError: If jsparams is not a string.
         KeyError: If a requested key is not present, or if the JSON string does
             not contain the expected PARAMS -> DICT structure.
     """
    if not isinstance(jsparams, str):
        raise TypeError(f"jsparams must be a string, got {type(jsparams).__name__}")
    params = json.loads(jsparams)

    if not isinstance(params, dict):
        raise KeyError("Invalid structure: JSON root must be a dictionary")

    source_dict = _extract_params_dict(params)

    result = {}
    for k in args:
        if k not in source_dict:
            raise KeyError(f"Parameter '{k}' not found in serialized object")
        result[k] = _from_serializable_dict(source_dict[k])
    return result