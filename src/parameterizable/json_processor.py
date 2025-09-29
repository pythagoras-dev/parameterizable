"""JSON-compatible serialization helpers for complex Python objects.

This module provides functions to convert rich Python data structures into a
JSON-serializable representation and back. It supports primitive types as well
as containers (list, tuple, set, dict) and certain custom objects.

The serialized form is a pure-JSON structure containing only dicts, lists,
strings, numbers, booleans, and null. Special container and object types are
encoded using internal marker keys.

"""

import importlib
import json
import types
from enum import Enum
from typing import Any, Mapping


_UNSUPPORTED_TYPES = (
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
        TUPLE: Marker key for tuple values. The value is a list of items.
        SET: Marker key for set values. The value is a list of items.
        CLASS: Name of the object's class used during reconstruction.
        MODULE: Name of the module where the object's class is defined.
        PARAMS: Serialized mapping of constructor parameters for ``get_params``
            based reconstruction.
        STATE: Serialized state for ``__getstate__``/``__setstate__`` based
            reconstruction.
    """

    DICT = "...DICT..."
    TUPLE = "...TUPLE..."
    SET = "...SET..."
    CLASS = "...CLASS..."
    MODULE = "...MODULE..."
    PARAMS = "...PARAMETERS..."
    STATE = "...STATE..."
    ENUM = "...ENUM..."


def _collect_object_state(obj: Any) -> dict:
    """Collect attributes from __dict__ and __slots__ across the class hierarchy.

    Traverses the method resolution order (MRO) to gather values defined in
    ``__slots__`` for each class, and merges them with the instance ``__dict__``
    when present. Missing slot attributes are ignored.

    Args:
        obj: The object whose state should be collected.

    Returns:
        A flat dictionary of attribute names to values representing the object's
        state suitable for further serialization.
    """
    state: dict[str, Any] = {}

    # Collect from __slots__ across the MRO
    for cls in type(obj).__mro__:
        if not hasattr(cls, "__slots__"):
            continue
        slots = cls.__slots__
        if isinstance(slots, str):
            slots = [slots]
        for name in slots:
            if name in ("__dict__", "__weakref__"):
                continue
            try:
                state[name] = getattr(obj, name)
            except AttributeError:
                # Slot not set on instance
                pass

    # Collect from __dict__ if available
    if hasattr(obj, "__dict__"):
        state.update(obj.__dict__)
    return state

def _to_serializable_dict(x: Any, seen: set[int] | None = None) -> Any:
    """Convert a Python object into a JSON-serializable structure.

    The transformation is recursive and supports primitives, lists, tuples,
    sets, and dicts. Certain custom objects are supported either through
    a ``get_params()`` method or the pickle protocol ``__getstate__()``.

    Args:
        x: The object to convert.
        seen:  A set of visited object ids for cycle detection.

    Returns:
        A structure composed only of JSON-compatible types (dict, list, str,
        int, float, bool, None), potentially enhanced with internal marker
        keys to represent tuples, sets, and reconstructable objects.

    Raises:
        TypeError: If ``x`` (or any nested value) contains an unsupported type.

    Examples:
        - Tuples and sets are encoded with markers:

          >>> _to_serializable_dict((1, 2))
          {'...TUPLE...': [1, 2]}
          >>> _to_serializable_dict({1, 2})
          {'...SET...': [1, 2]}
    """

    match x:
        case None | bool() | int() | float() | str():
            return x

    if isinstance(x, _UNSUPPORTED_TYPES):
        raise TypeError(f"Unsupported type: {type(x).__name__}")

    if seen is None:
        seen = set()

    obj_id = id(x)
    if obj_id in seen:
        raise RecursionError(
            f"Cyclic reference detected while serializing object of type {type(x).__name__}")
    seen.add(obj_id)

    try:
        match x:
            case obj if hasattr(obj, "get_params"):
                result = _process_state(obj.get_params(), obj, _Markers.PARAMS, seen)

            case list():
                result = [_to_serializable_dict(i, seen) for i in x]
            case tuple():
                result = {_Markers.TUPLE: [_to_serializable_dict(i, seen) for i in x]}
            case set():
                result = {_Markers.SET: [_to_serializable_dict(i, seen) for i in x]}
            case dict():
                # Keep plain dict when keys are strings; use DICT marker otherwise
                if all(isinstance(k, str) for k in x.keys()):
                    result = {k: _to_serializable_dict(v, seen) for k, v in x.items()}
                else:
                    result = {
                        _Markers.DICT: [
                            [_to_serializable_dict(k, seen), _to_serializable_dict(v, seen)]
                            for k, v in x.items()
                        ]
                    }
            case Enum():
                result = {
                    _Markers.ENUM: x.name,
                    _Markers.CLASS: x.__class__.__qualname__,
                    _Markers.MODULE: x.__class__.__module__,
                }

            case obj if hasattr(obj, "__getstate__"):
                result = _process_state(obj.__getstate__(), obj, _Markers.STATE, seen)
            case obj if hasattr(obj, "__dict__") or hasattr(obj.__class__, "__slots__"):
                result = _process_state(_collect_object_state(obj), obj, _Markers.STATE, seen)
            case _:
                raise TypeError(f"Unsupported type: {type(x).__name__}")
    finally:
        seen.remove(obj_id)
    return result


def _process_state(state: Any, obj: Any, marker: str, seen: set[int]) -> dict:
    """Wrap object identity and state into a marker-bearing mapping.

    Produces a dictionary containing the object's class and module names along
    with the provided state under the specified marker (e.g., ``PARAMS`` or
    ``STATE``). The state is recursively converted to JSON-serializable types.

    Args:
        state: The object's state, e.g. from `__getstate__()`.
        obj: The object being serialized (used to extract class/module names).
        marker: Which marker to use for the state payload.
        seen: A set of visited object ids for cycle detection.

    Returns:
        A dictionary suitable for JSON encoding that can be used by
        _recreate_object() to rebuild the instance.
    """

    return {_Markers.CLASS: obj.__class__.__qualname__,
        _Markers.MODULE: obj.__class__.__module__,
        marker: _to_serializable_dict(state, seen)}


def _get_all_slots(cls: type) -> list[str]:
    """Collect all slot names from a class hierarchy, excluding special ones."""
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

    The input mapping must include ``MODULE`` and ``CLASS`` markers and either
    ``PARAMS`` (constructor parameters) or ``STATE`` (instance state).

    Args:
        x: Marker-bearing mapping produced by _to_serializable_dict() for
           custom objects.

    Returns:
        A new instance of the referenced class reconstructed from parameters or
        state.

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
                # This branch handles tuple state, typically from __getstate__
                # for classes with __slots__.
                slots_to_fill = _get_all_slots(cls)

                slot_values, dict_values = (None, None)

                # For classes with __dict__ in __slots__, state can be a 2-tuple (slot_values, dict_values)
                # where dict_values can be None if the dict is empty.
                if len(state) == 2 and (state[1] is None or isinstance(state[1], dict)):
                    slot_values, dict_values = state
                else:
                    # Otherwise, state is just a tuple of slot values
                    slot_values = state

                if dict_values:
                    for k, v in dict_values.items():
                        setattr(obj, k, v)

                # slot_values can be an empty tuple or None for some __getstate__ impls
                if slot_values:
                    if len(slot_values) != len(slots_to_fill):
                        raise TypeError(
                            f"Tuple state length {len(slot_values)} does not match "
                            f"slots length {len(slots_to_fill)} for class {cls.__name__}")
                    for value, name in zip(slot_values, slots_to_fill):
                        setattr(obj, name, value)

            else: # Fallback reconstruction
                for k, v in state.items():
                    setattr(obj, k, v)
            return obj
        case _:
            raise TypeError("Unable to recreate object from provided data")


def _from_serializable_dict(x: Any) -> Any:
    """Inverse of function _to_serializable_dict()

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
            if not isinstance(val, list):
                raise TypeError("DICT marker must map to a list of lists")
            pairs: list[tuple[Any, Any]] = []
            for item in val:
                if not (isinstance(item, (list, tuple)) and len(item) == 2):
                    raise TypeError("DICT marker must map to a list of 2-item pairs")
                pairs.append((item[0], item[1]))
            return {_from_serializable_dict(k): _from_serializable_dict(v)
                    for k, v in pairs}
        case {_Markers.MODULE: _, **__} | {_Markers.CLASS: _, **__} as d:
            return _recreate_object(d)
        case dict() as d:
            return {k: _from_serializable_dict(v) for k, v in d.items()}
        case _:
            raise TypeError(f"Unsupported type: {type(x).__name__}")


def dumps(obj: Any, **kwargs) -> str:
    """Dump an object to a JSON string using the custom serialization rules.

    Args:
        obj: The object to serialize.
        **kwargs: Additional keyword arguments forwarded to
            `json.dumps` (e.g., ``indent=2``, ``sort_keys=True``).

    Returns:
        The JSON string representing the object.
    """
    return json.dumps(_to_serializable_dict(obj), **kwargs)


def loads(s: str, **kwargs) -> Any:
    """Load an object from a JSON string produced by dumps().

    Args:
        s: The JSON string to parse.
        **kwargs: Additional keyword arguments forwarded to
            `json.loads` (``object_hook`` is not allowed here).

    Returns:
        The Python object reconstructed from the JSON string.
    """
    if "object_hook" in kwargs:
        raise ValueError("object_hook cannot be used with "
                         "parametetizable.loads()")
    return _from_serializable_dict(json.loads(s, **kwargs))