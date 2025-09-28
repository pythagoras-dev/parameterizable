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
from enum import Enum
from typing import Any, Mapping


class _Markers(str, Enum):
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

    TUPLE = "..tuple.."
    SET = "..set.."
    CLASS = "..class.."
    MODULE = "..module.."
    PARAMS = "..parameters.."
    STATE = "..state.."


def _collect_object_state(obj: Any) -> dict:
    """Collect instance attributes from __dict__ and __slots__ recursively."""
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

def _to_serializable_dict(x: Any) -> Any:
    """Convert a Python object into a JSON-serializable structure.

    The transformation is recursive and supports primitives, lists, tuples,
    sets, and dicts with string keys. Certain custom objects are supported
    either through a ``get_params()`` method or the pickle protocol
    ``__getstate__()``.

    Args:
        x: The object to convert.

    Returns:
        A structure composed only of JSON-compatible types (dict, list, str,
        int, float, bool, None), potentially enhanced with internal marker
        keys to represent tuples, sets, and reconstructable objects.

    Raises:
        TypeError: If ``x`` (or any nested value) contains an unsupported type,
            or if a dictionary contains a non-string key.

    Examples:
        - Tuples and sets are encoded with markers:

          >>> _to_serializable_dict((1, 2))
          {'..tuple..': [1, 2]}
          >>> _to_serializable_dict({1, 2})
          {'..set..': [1, 2]}

        - Dict keys must be strings:

          >>> _to_serializable_dict({1: 'a'})
          Traceback (most recent call last):
          ...
          TypeError: Dictionary key must be a string, but got: int
    """
    match x:
        case None | bool() | int() | float() | str():
            return x
        case list():
            return [_to_serializable_dict(i) for i in x]
        case tuple():
            return {_Markers.TUPLE: [_to_serializable_dict(i) for i in x]}
        case set():
            return {_Markers.SET: [_to_serializable_dict(i) for i in x]}
        case dict():
            return _process_dict(x)
        case obj if hasattr(obj, "get_params"):
            return _process_state(obj.get_params(), obj, _Markers.PARAMS)
        case obj if hasattr(obj, "__getstate__"):
            return _process_state(obj.__getstate__(), obj, _Markers.STATE)
        case obj if hasattr(obj, "__dict__") or hasattr(obj.__class__, "__slots__"):
            return _process_state(_collect_object_state(obj), obj, _Markers.STATE)
        case _:
            raise TypeError(f"Unsupported type: {type(x).__name__}")

def _process_dict(x:dict)->dict:
    result = {}
    for k, v in x.items():
        if not isinstance(k, str):
            raise TypeError(f"Dictionary key must be a string, "
                            f"but got: {type(k).__name__}")
        result[k] = _to_serializable_dict(v)
    return result

def _process_state(state:dict, obj:Any, marker:str) -> dict:
    return {
        _Markers.CLASS: obj.__class__.__name__,
        _Markers.MODULE: obj.__class__.__module__,
        marker: _to_serializable_dict(state),
    }



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
                        "'..module..' and '..class..'")

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
        case {_Markers.STATE: state_json}:
            state = _from_serializable_dict(state_json)
            obj = cls.__new__(cls)
            if hasattr(obj, "__setstate__"):
                obj.__setstate__(state)
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
            if not isinstance(val, list):
                raise TypeError("Tuple marker must map to a list")
            return tuple(_from_serializable_dict(i) for i in val)
        case {_Markers.SET: val}:
            if not isinstance(val, list):
                raise TypeError("Set marker must map to a list")
            return set(_from_serializable_dict(i) for i in val)
        case {_Markers.MODULE: _, **__} as d:
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
            :func:`json.loads` (e.g., ``object_hook`` is not used here).

    Returns:
        The Python object reconstructed from the JSON string.
    """
    return _from_serializable_dict(json.loads(s, **kwargs))