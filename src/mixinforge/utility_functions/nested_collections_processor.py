"""Stack-based traversal of nested structures with cycle detection.

Provides functions to traverse and extract elements from deeply nested
composite objects including collections, mappings, and custom objects.
Uses iterative algorithms to avoid recursion depth limits.
"""
from collections import deque
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, TypeVar
from itertools import chain
from collections import defaultdict, OrderedDict, Counter, ChainMap
from weakref import WeakKeyDictionary, WeakValueDictionary
from types import GetSetDescriptorType, MappingProxyType


from ..utility_functions.atomics_detector import is_atomic_object, is_atomic_type

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
    seen = set()
    for base_cls in cls.__mro__:
        if hasattr(base_cls, '__slots__'):
            cls_slots = base_cls.__slots__
            if isinstance(cls_slots, str):
                cls_slots = [cls_slots]

            for s in cls_slots:
                if s not in seen and s not in ('__dict__', '__weakref__'):
                    slots.append(s)
                    seen.add(s)
    return slots


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
    return type(obj) in {
        dict,
        defaultdict,
        OrderedDict,
        Counter,
        ChainMap,
        WeakKeyDictionary,
        WeakValueDictionary,
        MappingProxyType}


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
    return type(obj) in {list, tuple, set, frozenset, deque}


_MISSING = object()  # private sentinel

def _yield_attributes(obj: Any) -> Iterator[Any]:
    """Safely yield attribute values from an object's __dict__ and/or __slots__.

    The function is defensive against expensive or side-effect-prone attribute
    access:

    * Attributes obtained directly from ``__dict__`` are yielded as-is.
    * For ``__slots__`` we:
        1. Collect *all* slot names from the MRO (`_get_all_slots`).
        2. Check the descriptor on the class *before* access to skip properties
           and other active descriptors.
        3. Fetch the attribute via ``getattr`` safely.

    Note that *data* descriptors defined at class level (e.g. ``@property``)
    are intentionally skipped because reading them could trigger arbitrary
    code execution.
    """
    # 1. Attributes stored in __dict__ are always safe to yield
    if hasattr(obj, "__dict__"):
        yield from obj.__dict__.values()

    # 2. Handle __slots__ (may also appear in parent classes)
    if hasattr(obj.__class__, "__slots__"):
        for slot_name in _get_all_slots(obj.__class__):
            # Fast path: ignore special/dunder names
            if slot_name.startswith("__"):
                continue

            # Skip class-level descriptors that aren't per-instance data
            # Check descriptor BEFORE triggering potential property side-effects
            class_attr = getattr(obj.__class__, slot_name, _MISSING)
            if isinstance(
                class_attr,
                (
                    property,
                    staticmethod,
                    classmethod,
                    # Note: MemberDescriptorType (slots) is intentionally OMITTED
                    # from this list because it represents
                    # the actual slots we want to read.
                    GetSetDescriptorType,
                ),
            ):
                continue

            try:
                value = getattr(obj, slot_name, _MISSING)
            except Exception:
                continue

            if value is _MISSING or value is class_attr:
                # Slot not initialised on this instance
                continue

            yield value

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
        return iter(())

    if _is_standard_mapping(obj):
        yield from _create_mapping_iterator(obj, traverse_dict_keys)
    elif _is_standard_iterable(obj):
        yield from obj
    elif isinstance(obj, Mapping):
        yield from chain(_yield_attributes(obj), _create_mapping_iterator(obj, traverse_dict_keys))
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
    matrices, or paths. The function traverses nested iterables, yielding
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

    if not isinstance(obj, Iterable) or is_atomic_object(obj):
        raise TypeError(f"Expected a non-atomic Iterable as input, "
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

            item_iter = _create_mapping_iterator(item, traverse_dict_keys) if isinstance(item, Mapping) else iter(item)
            seen_ids.add(obj_id)
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

    stack: deque[tuple[Iterator[Any], set[int]]] = deque([(iter([obj]), set())])
    seen_ids: set[int] = set()

    while stack:
        it, path = stack[-1]
        try:
            current = next(it)
        except StopIteration:
            stack.pop()
            continue

        obj_id = id(current)

        if obj_id in path:
            raise ValueError(
                f"Cyclic reference detected at object {repr(current)} "
                f"(id={obj_id})")

        if obj_id in seen_ids:
            continue

        seen_ids.add(obj_id)

        if isinstance(current, target_type):
            yield current

        if is_atomic_object(current):
            continue

        children_iter = _get_children_from_object(current, traverse_dict_keys)
        stack.append((children_iter, path | {obj_id}))