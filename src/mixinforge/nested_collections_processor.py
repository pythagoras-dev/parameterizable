"""Stack-based traversal of nested structures with cycle detection.

Provides functions to traverse and extract elements from deeply nested
composite objects including collections, mappings, and custom objects.
Uses iterative algorithms to avoid recursion depth limits.
"""
from collections import deque
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, TypeVar
from itertools import chain

from .atomics_detector import is_atomic_object, is_atomic_type

T = TypeVar('T')


def _create_mapping_iterator(mapping: Mapping, traverse_dict_keys: bool) -> Iterator[Any]:
    """Create iterator from mapping, optionally including keys.

    Args:
        mapping: Mapping to iterate over.
        traverse_dict_keys: If True, yields keys then values; otherwise yields values only.

    Returns:
        Iterator over values only, or over keys then values.
    """
    if traverse_dict_keys:
        return chain(mapping.keys(), mapping.values())
    return iter(mapping.values())


def _get_all_slots(cls: type) -> list[str]:
    """Collect slot names from class hierarchy.

    Args:
        cls: Class to inspect for __slots__.

    Returns:
        Slot names from all base classes, excluding __dict__ and __weakref__.
    """
    slots = []
    for base_cls in cls.__mro__:
        if hasattr(base_cls, '__slots__'):
            cls_slots = base_cls.__slots__
            if isinstance(cls_slots, str):
                cls_slots = [cls_slots]
            slots.extend(cls_slots)
    return [s for s in slots if s not in ('__dict__', '__weakref__')]


def _is_standard_mapping(obj: Any) -> bool:
    """Check if object is a standard mapping type.

    Standard mappings include built-in dict and common stdlib mapping types
    from collections, weakref, and types modules. These are treated as pure
    data containers and only their keys/values are traversed, not their
    internal attributes.

    Args:
        obj: Object to check.

    Returns:
        True if object is a standard library mapping type.
    """
    from collections import defaultdict, OrderedDict, Counter, ChainMap
    from weakref import WeakKeyDictionary, WeakValueDictionary
    from types import MappingProxyType

    return isinstance(obj, (
        dict,
        defaultdict,
        OrderedDict,
        Counter,
        ChainMap,
        WeakKeyDictionary,
        WeakValueDictionary,
        MappingProxyType,
    ))


def _is_standard_iterable(obj: Any) -> bool:
    """Check if object is a standard iterable collection type.

    Standard iterables include built-in sequences and sets, plus common
    stdlib collection types. These are treated as pure data containers
    and only their items are traversed, not their internal attributes.

    Args:
        obj: Object to check.

    Returns:
        True if object is a standard library iterable type.
    """
    return isinstance(obj, (list, tuple, set, frozenset, deque))


def _yield_attributes(obj: Any) -> Iterator[Any]:
    """Yield attribute values from object's __dict__ or __slots__.

    Extracts all accessible attributes from an object, checking __dict__
    first, then falling back to __slots__ if present. This is used to
    traverse custom objects that may contain child objects in their
    attributes.

    Args:
        obj: Object to extract attributes from.

    Yields:
        Attribute values from __dict__ or __slots__.
    """
    if hasattr(obj, '__dict__'):
        yield from obj.__dict__.values()
    elif hasattr(obj.__class__, '__slots__'):
        for slot_name in _get_all_slots(obj.__class__):
            try:
                yield getattr(obj, slot_name)
            except AttributeError:
                continue


def _get_children_from_object(obj: Any, traverse_dict_keys: bool) -> Iterator[Any]:
    """Extract child objects for traversal from any object type.

    Uses a refined traversal strategy:
    - Standard collections (dict, list, set, deque, etc.): iterate only
    - Custom iterables: yield attributes + iterated items
    - Non-iterable objects: yield attributes only

    This ensures standard library collections are treated as pure data
    containers, while custom objects with both iteration and attributes
    get full introspection.

    Args:
        obj: Object to extract children from.
        traverse_dict_keys: Whether to include mapping keys along with values.

    Yields:
        Child objects to traverse.
    """
    if is_atomic_object(obj):
        return

    if _is_standard_mapping(obj):
        yield from _create_mapping_iterator(obj, traverse_dict_keys)
    elif _is_standard_iterable(obj):
        yield from obj
    elif isinstance(obj, Iterable):
        yield from chain(_yield_attributes(obj), obj)
    else:
        yield from _yield_attributes(obj)


def _is_traversable_collection(obj: Any) -> bool:
    """Check if object should be traversed or yielded as atomic leaf.

    Args:
        obj: Object to check.

    Returns:
        True to traverse inside, False to yield as atomic.
    """
    if is_atomic_object(obj):
        return False
    if not isinstance(obj, Iterable):
        return False
    return True


def find_atomics_in_nested_collections(
    obj: Iterable[Any],
    *,
    traverse_dict_keys: bool = False
) -> Iterator[Any]:
    """Yield atomic elements from nested collections with weak deduplication.

    Atomic elements are indivisible leaf values such as numbers, strings,
    matrices, or paths. The function raverses nested iterables, yielding
    only atomic elements. Their exact order and complete deduplication
    are not guaranteed.

    Args:
        obj: The root collection to traverse.
        traverse_dict_keys: If True, includes mapping keys in the traversal.

    Yields:
        Atomic elements in depth-first order, deduplicated by identity.

    Raises:
        TypeError: If obj is not an iterable.
        ValueError: If a cycle is detected.
    """
    if not isinstance(obj, Iterable):
        raise TypeError(f"Expected an Iterable as input, "
                        f"got {type(obj).__name__} instead")

    root_iter = _create_mapping_iterator(obj, traverse_dict_keys) if isinstance(obj, Mapping) else iter(obj)
    root_id   = id(obj)

    stack: deque[tuple[Iterator[Any], set[int]]] = deque([(root_iter, {root_id})])
    seen_ids: set[int] = {root_id}

    while stack:
        it, path = stack[-1]
        try:
            item = next(it)
        except StopIteration:
            stack.pop()
            continue

        obj_id = id(item)
        if _is_traversable_collection(item):
            if obj_id in path:
                raise ValueError(f"Cyclic reference detected at {obj_id}")
            if obj_id in seen_ids:
                continue

            seen_ids.add(obj_id)
            item_iter = _create_mapping_iterator(item, traverse_dict_keys) if isinstance(item, Mapping) else iter(item)
            stack.append((item_iter, path | {obj_id}))
        else:
            if obj_id in seen_ids:
                continue
            seen_ids.add(obj_id)
            yield item


def find_nonatomics_inside_composite_object(
    obj: Any,
    target_type: type[T],
    *,
    traverse_dict_keys: bool = False
) -> Iterator[T]:
    """Find all instances of a composite type within any object.

    Performs traversal of iterables, mappings, and custom objects
    (via __dict__ and __slots__). Yields all instances of target_type,
    continuing to search inside matched objects for nested instances.
    Exact return order and complete deduplication are not guaranteed.

    Args:
        obj: The object to search within.
        target_type: The composite type to search for.
        traverse_dict_keys: If True, includes mapping keys in the traversal.

    Yields:
        Instances of target_type in depth-first order, deduplicated by identity.

    Raises:
        TypeError: If target_type is atomic.
        ValueError: If a cycle is detected.

    Example:
        >>> class Config:
        ...     def __init__(self, name):
        ...         self.name = name
        ...         self.nested = None
        >>> c1 = Config("main")
        >>> c2 = Config("sub")
        >>> c1.nested = c2
        >>> obj = {"config": c1, "data": [1, 2, 3]}
        >>> configs = list(find_nonatomics_inside_composite_object(obj, Config))
        >>> len(configs)
        2
    """

    if is_atomic_type(target_type):
        raise TypeError(
            f"target_type must be a non-atomic type, "
            f"got atomic type: {target_type.__name__}"
        )

    stack: deque[tuple[Any, set[int]]] = deque([(obj, set())])
    seen_ids: set[int] = set()

    while stack:
        current, path = stack.pop()
        obj_id = id(current)

        if obj_id in path:
            raise ValueError(f"Cyclic reference detected at object id {obj_id}")

        if obj_id in seen_ids:
            continue

        seen_ids.add(obj_id)

        if isinstance(current, target_type):
            yield current

        new_path = path | {obj_id}
        for child in _get_children_from_object(current, traverse_dict_keys):
            stack.append((child, new_path))