"""Stack-based traversal and introspection of nested structures.

Provides functions to traverse and extract elements from deeply nested
composite objects including collections, mappings, and custom objects.
"""
from collections import deque, defaultdict, OrderedDict, Counter, ChainMap
from collections.abc import Iterable, Iterator, Mapping, Callable
from types import GetSetDescriptorType, MappingProxyType, UnionType
from typing import Any, Final, Optional, TypeAlias, TypeVar
from itertools import chain
from weakref import WeakKeyDictionary, WeakValueDictionary

from ..utility_functions.atomics_detector import is_atomic_object

T = TypeVar('T')

# Type alias matching isinstance()'s classinfo parameter.
# Supports: single type, tuple of types (recursively), or union types (int | str).
ClassInfo: TypeAlias = type | UnionType | tuple["ClassInfo", ...]


def _is_valid_classinfo(classinfo: Any) -> bool:
    """Check if classinfo is valid for isinstance() usage.

    Args:
        classinfo: Value to validate.

    Returns:
        True if classinfo is a type, UnionType, or tuple of valid classinfo values.
    """
    if isinstance(classinfo, (type, UnionType)):
        return True
    if isinstance(classinfo, tuple):
        return all(_is_valid_classinfo(item) for item in classinfo)
    return False


# ==============================================================================
# Introspection Helpers
# ==============================================================================

def _get_all_slots(cls: type) -> list[str]:
    """Collect slot names from class hierarchy.

    Args:
        cls: Class to inspect.

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
    """Check if object is a standard mapping type (dict, Counter, etc.)."""
    return type(obj) in {
        dict,
        defaultdict,
        OrderedDict,
        Counter,
        ChainMap,
        WeakKeyDictionary,
        WeakValueDictionary,
        MappingProxyType} or isinstance(obj, defaultdict)


def _is_standard_iterable(obj: Any) -> bool:
    """Check if object is a standard iterable collection type (list, set, etc.)."""
    return type(obj) in {list, tuple, set, frozenset, deque}


_MISSING: Final = object()  # private sentinel


def _yield_attributes(obj: Any) -> Iterator[Any]:
    """Safely yield attribute values from an object's __dict__ and/or __slots__.

    Attributes from ``__dict__`` are yielded as-is. For ``__slots__``,
    descriptors are checked before access to avoid triggering side effects
    (like properties).

    Yields:
        Attribute values from the object.

    Note:
        Class-level data descriptors (e.g. @property) are skipped to prevent
        arbitrary code execution.
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


# ==============================================================================
# Traversal Logic
# ==============================================================================

def _create_standard_mapping_iterator(mapping: Mapping) -> Iterator[Any]:
    return chain(mapping.keys(), mapping.values())


def _get_children_from_object(obj: Any) -> Iterator[Any]:
    """Extract child objects for traversal from any object type.

    Standard collections are treated as pure data containers (iterated only).
    Custom objects yield both attributes and iterated items (if iterable).

    Args:
        obj: Object to extract children from.

    Returns:
        Iterator of child objects to traverse.
    """
    if is_atomic_object(obj):
        return iter(())

    if _is_standard_mapping(obj):
        return _create_standard_mapping_iterator(obj)

    if _is_standard_iterable(obj):
        return iter(obj)

    if isinstance(obj, Mapping):
        # Optimization: treat as standard mapping if no instance attributes
        # (avoid overhead of chaining generators if __dict__ is empty and no __slots__)
        # This is critical for performance when traversing deep structures of
        # dict subclasses (like KwArgs in Pythagoras) to avoid massive slowdowns.
        if (isinstance(obj, dict)
                and not hasattr(obj.__class__, "__slots__")
                and hasattr(obj, "__dict__")
                and not obj.__dict__):
            return _create_standard_mapping_iterator(obj)

        return chain(_yield_attributes(obj), _create_standard_mapping_iterator(obj))

    if isinstance(obj, Iterable):
        return chain(_yield_attributes(obj), obj)

    return _yield_attributes(obj)


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


def _traverse(root: Any, get_children_fn: Callable[[Any], Optional[Iterator[Any]]]) -> Iterator[Any]:
    """Generic stack-based traversal generator.
    
    Yields every visited object (including root).
    
    Args:
        root: Starting object.
        get_children_fn: Function returning iterator of children or None if no traversal.
        
    Yields:
        All reachable objects in depth-first order.
    """
    stack: deque[Iterator[Any]] = deque([iter([root])])
    seen_ids: set[int] = set()

    while stack:
        it = stack[-1]
        try:
            current = next(it)
        except StopIteration:
            stack.pop()
            continue

        obj_id = id(current)
        if obj_id in seen_ids:
            continue
            
        seen_ids.add(obj_id)
        yield current
        
        children = get_children_fn(current)
        if children is not None:
            stack.append(children)


def flatten_nested_collection(obj: Iterable[Any]) -> Iterator[Any]:
    """Yield leaf elements from nested collections with weak deduplication.

    Atomic elements are indivisible values such as numbers, strings,
    matrices, or paths. The function traverses nested iterables, yielding
    leaf values, which includes both atomics and non-iterable objects.
    Their exact order and complete deduplication are not guaranteed.

    Handles cycles gracefully by visiting each object only once.

    Mapping keys and values are both traversed.

    Args:
        obj: The root collection to traverse.

    Yields:
        Atomic elements in depth-first order, deduplicated by identity.

    Raises:
        TypeError: If obj is not an iterable.
    """

    if not isinstance(obj, Iterable) or is_atomic_object(obj):
        raise TypeError(f"Expected a non-atomic Iterable as input, "
                        f"got {type(obj).__name__} instead")

    def _get_children(item: Any) -> Optional[Iterator[Any]]:
        if _is_traversable_collection(item):
            if isinstance(item, Mapping):
                return _create_standard_mapping_iterator(item)
            return iter(item)
        return None

    for item in _traverse(obj, _get_children):
        if not _is_traversable_collection(item):
            yield item


def find_instances_inside_composite_object(
    obj: Any,
    classinfo: ClassInfo,
    deep_search: bool = True
) -> Iterator[Any]:
    """Find all instances of a target type within any object.

    Performs traversal of iterables, mappings, and custom objects
    (via __dict__ and __slots__). Yields all instances matching classinfo,
    continuing to search inside matched objects for nested instances.
    Exact return order and complete deduplication are not guaranteed.

    Handles cycles gracefully by visiting each object only once.

    Mapping keys and values are both traversed.

    Args:
        obj: The object to search within.
        classinfo: Type or tuple of types to search for. Accepts the same
            values as the second argument to isinstance(): a single type,
            a tuple of types (recursively), or a union type (e.g., int | str).
        deep_search: If True (default), after finding an instance, continue
            recursively searching inside it for more matching instances.
            If False, stop traversal at matched instances.

    Yields:
        Instances matching classinfo in depth-first order, deduplicated by identity.

    Raises:
        TypeError: If classinfo is not a valid type specification (must be a
            type, tuple of types, or union type).
    """
    if not _is_valid_classinfo(classinfo):
        raise TypeError(
            f"classinfo must be a type, tuple of types, or union type, "
            f"got {type(classinfo).__name__}"
        )

    def _get_children(item: Any) -> Optional[Iterator[Any]]:
        if is_atomic_object(item):
            return None
        if not deep_search and isinstance(item, classinfo):
            return None
        return _get_children_from_object(item)

    for item in _traverse(obj, _get_children):
        if isinstance(item, classinfo):
            yield item
