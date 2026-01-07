"""Stack-based traversal of nested structures with cycle detection.

Provides functions to traverse and extract elements from deeply nested
composite objects including collections, mappings, and custom objects.
Uses iterative algorithms to avoid recursion depth limits.
"""
from collections import deque
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, TypeVar

T = TypeVar('T')

from .atomics_detector import is_atomic_object


def _create_mapping_iterator(mapping: Mapping, traverse_dict_keys: bool) -> Iterator[Any]:
    """Create iterator from mapping, optionally including keys.

    Args:
        mapping: Mapping to iterate over.
        traverse_dict_keys: Whether to include both keys and values.

    Returns:
        Iterator over values only, or over keys then values.
    """
    if traverse_dict_keys:
        from itertools import chain
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


def _get_children_from_object(obj: Any, traverse_dict_keys: bool) -> Iterator[Any]:
    """Extract child objects for traversal from any object type.

    Args:
        obj: Object to extract children from.
        traverse_dict_keys: Whether to include mapping keys along with values.

    Yields:
        Child objects to traverse.
    """
    if is_atomic_object(obj):
        return

    if isinstance(obj, Mapping):
        yield from _create_mapping_iterator(obj, traverse_dict_keys)
    elif isinstance(obj, Iterable):
        yield from obj
    elif hasattr(obj, '__dict__'):
        yield from obj.__dict__.values()
    elif hasattr(obj.__class__, '__slots__'):
        for slot_name in _get_all_slots(obj.__class__):
            try:
                yield getattr(obj, slot_name)
            except AttributeError:
                continue


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
    """Yield atomic elements from nested collection with deduplication.

    Atomic elements are indivisible leaf values such as numbers, strings,
    matrices, or paths. Traverses nested iterables depth-first, yielding
    only atomic elements. Each object is yielded at most once based on
    identity.

    Args:
        obj: Nested collection to traverse.
        traverse_dict_keys: Whether to traverse mapping keys along with values.

    Yields:
        Atomic elements in depth-first order, deduplicated by identity.

    Raises:
        TypeError: If obj is not iterable.
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

    Performs depth-first traversal of iterables, mappings, and custom objects
    (via __dict__ and __slots__). Yields all instances of target_type,
    continuing to search inside matched objects for nested instances.

    Args:
        obj: Object to search within.
        target_type: Composite type to find. Atomic types are not allowed.
        traverse_dict_keys: Whether to traverse mapping keys along with values.

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
    from .atomics_detector import is_atomic_type

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