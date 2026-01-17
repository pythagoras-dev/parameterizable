"""Stack-based traversal of nested structures with cycle detection.

Provides functions to traverse and extract elements from deeply nested
composite objects including collections, mappings, and custom objects.
Uses iterative algorithms to avoid recursion depth limits.
"""
from collections import deque
from collections.abc import Iterable, Iterator, Mapping, Callable
from typing import Any, TypeVar, Optional
from itertools import chain
from collections import defaultdict, OrderedDict, Counter, ChainMap
from weakref import WeakKeyDictionary, WeakValueDictionary
from types import GetSetDescriptorType, MappingProxyType
from dataclasses import replace, fields

from ..utility_functions.atomics_detector import is_atomic_object, is_atomic_type

T = TypeVar('T')


def _create_mapping_iterator(mapping: Mapping) -> Iterator[Any]:
    """Create iterator from mapping, including both keys and values.

    Args:
        mapping: Mapping to iterate over.

    Returns:
        Iterator over keys then values.
    """
    return chain(mapping.keys(), mapping.values())


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

def _get_children_from_object(obj: Any) -> Iterator[Any]:
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

    Yields:
        Child objects to traverse.
    """
    if is_atomic_object(obj):
        return iter(())

    if _is_standard_mapping(obj):
        yield from _create_mapping_iterator(obj)
    elif _is_standard_iterable(obj):
        yield from obj
    elif isinstance(obj, Mapping):
        yield from chain(_yield_attributes(obj), _create_mapping_iterator(obj))
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


def _traverse(root: Any, get_children_fn: Callable[[Any], Optional[Iterator[Any]]]) -> Iterator[Any]:
    """Generic stack-based traversal generator.
    
    Yields every visited object (including root).
    Uses get_children_fn to determine if and how to traverse children.
    
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
                return _create_mapping_iterator(item)
            return iter(item)
        return None

    for item in _traverse(obj, _get_children):
        if not _is_traversable_collection(item):
            yield item


def find_instances_inside_composite_object(
    obj: Any,
    target_type: type[T]
) -> Iterator[T]:
    """Find all instances of a target type within any object.

    Performs traversal of iterables, mappings, and custom objects
    (via __dict__ and __slots__). Yields all instances of target_type,
    continuing to search inside matched objects for nested instances.
    Exact return order and complete deduplication are not guaranteed.

    Handles cycles gracefully by visiting each object only once.

    Mapping keys and values are both traversed.

    Args:
        obj: The object to search within.
        target_type: The composite type to search for.

    Yields:
        Instances of target_type in depth-first order, deduplicated by identity.

    Raises:
        TypeError: If target_type is atomic.
    """
    
    def _get_children(item: Any) -> Optional[Iterator[Any]]:
        if is_atomic_object(item):
            return None
        return _get_children_from_object(item)

    for item in _traverse(obj, _get_children):
        if isinstance(item, target_type):
            yield item


class _ObjectReconstructor:
    """Helper class for recursive object reconstruction with cycle handling."""
    
    def __init__(self, target_type: type[Any], transform_fn: Callable[[Any], Any]):
        self.target_type = target_type
        self.transform_fn = transform_fn
        self.seen_ids: dict[int, Any] = {}

    def reconstruct(self, original: Any) -> Any:
        """Reconstruct an object, replacing transformed children."""
        obj_id = id(original)

        # If we've already reconstructed this object, return it
        # This handles cycles: we process each object once and reuse it
        if obj_id in self.seen_ids:
            return self.seen_ids[obj_id]

        # Atomic objects don't need reconstruction
        if is_atomic_object(original):
            self.seen_ids[obj_id] = original
            return original

        # Check if this is a target type instance
        if isinstance(original, self.target_type):
            # Mark as being processed to prevent infinite recursion
            self.seen_ids[obj_id] = original  # Temporary placeholder

            # Apply the transformation first
            transformed = self.transform_fn(original)

            # Now recursively process the transformed object's children
            # to replace any nested target instances
            transformed_reconstructed = self._reconstruct_object_attributes(transformed)

            self.seen_ids[obj_id] = transformed_reconstructed
            return transformed_reconstructed

        # Reconstruct collections by recursively processing children
        if _is_standard_mapping(original):
            # Mark as being processed to handle cycles
            result = type(original)()
            self.seen_ids[obj_id] = result

            changed = False
            for k, v in original.items():
                new_k = self.reconstruct(k)
                new_v = self.reconstruct(v)
                if new_k is not k or new_v is not v:
                    changed = True
                result[new_k] = new_v

            if not changed:
                # Nothing changed, return original
                self.seen_ids[obj_id] = original
                return original

            return result

        elif _is_standard_iterable(original):
            # For mutable iterables (list), create placeholder and fill it
            # For immutable (tuple, frozenset), we'll need to reconstruct after
            is_mutable = isinstance(original, list)

            if is_mutable:
                # Create empty list placeholder to handle cycles
                result = []
                self.seen_ids[obj_id] = result

                changed = False
                for item in original:
                    new_item = self.reconstruct(item)
                    if new_item is not item:
                        changed = True
                    result.append(new_item)

                if not changed:
                    # Nothing changed, return original
                    self.seen_ids[obj_id] = original
                    return original

                return result
            else:
                # Immutable types: mark with placeholder, then reconstruct
                self.seen_ids[obj_id] = original  # Temporary placeholder

                new_items = []
                changed = False
                for item in original:
                    new_item = self.reconstruct(item)
                    if new_item is not item:
                        changed = True
                    new_items.append(new_item)

                if not changed:
                    return original

                result = type(original)(new_items)
                self.seen_ids[obj_id] = result
                return result

        elif isinstance(original, Mapping):
            # Custom mapping with attributes
            new_dict = {}
            changed = False
            for k, v in original.items():
                new_k = self.reconstruct(k)
                new_v = self.reconstruct(v)
                if new_k is not k or new_v is not v:
                    changed = True
                new_dict[new_k] = new_v

            if changed:
                result = type(original)(new_dict)
                self.seen_ids[obj_id] = result
                return result

            self.seen_ids[obj_id] = original
            return original

        elif isinstance(original, Iterable):
            # Custom iterable with attributes
            new_items = []
            changed = False
            for item in original:
                new_item = self.reconstruct(item)
                if new_item is not item:
                    changed = True
                new_items.append(new_item)

            if changed:
                result = type(original)(new_items)
                self.seen_ids[obj_id] = result
                return result

            self.seen_ids[obj_id] = original
            return original

        else:
            # Non-iterable object with attributes (__dict__ or __slots__)
            # Use the same reconstruction logic as for target types
            result = self._reconstruct_object_attributes(original)
            self.seen_ids[obj_id] = result
            return result

    def _reconstruct_object_attributes(self, obj_to_process: Any) -> Any:
        """Reconstruct an object's attributes, replacing any target instances."""
        if is_atomic_object(obj_to_process):
            return obj_to_process

        # For dataclass or regular objects with __dict__ or __slots__
        if hasattr(obj_to_process, '__dict__') or hasattr(obj_to_process.__class__, '__slots__'):
            # Get all attributes
            children_list = list(_yield_attributes(obj_to_process))

            # Reconstruct each child
            new_children = []
            changed = False
            for child in children_list:
                new_child = self.reconstruct(child)
                new_children.append(new_child)
                if new_child is not child:
                    changed = True

            if not changed:
                return obj_to_process

            # Try to create a new instance with transformed attributes
            # For frozen dataclasses, we need to use replace or reconstruct
            if hasattr(obj_to_process, '__dataclass_fields__'):
                # It's a dataclass - use replace
                field_values = {}
                field_list = fields(obj_to_process)
                for field, new_value in zip(field_list, new_children):
                    field_values[field.name] = new_value
                return replace(obj_to_process, **field_values)
            else:
                # For other objects, we can't easily reconstruct, return as-is
                # (This limitation was present in the original code)
                return obj_to_process

        return obj_to_process


def transform_instances_inside_composite_object(
    obj: Any,
    target_type: type[T],
    transform_fn: Callable[[T], Any]
) -> Any:
    """Transform all instances of a target type within any object.

    Performs traversal of iterables, mappings, and custom objects
    (via __dict__ and __slots__). Transforms all instances of target_type
    using transform_fn and reconstructs the composite object with the
    transformed instances.

    If no instances of target_type are found, returns the original object
    unchanged.

    Handles cycles gracefully: each object is transformed only once, and
    cycle structure is preserved in the result.

    Mapping keys and values are both traversed and can be transformed.

    Args:
        obj: The object to search within and transform.
        target_type: The composite type to search for and transform.
        transform_fn: Function to apply to each instance of target_type.

    Returns:
        The transformed composite object, or the original if no matches found.

    Raises:
        TypeError: If target_type is atomic.
    """

    if is_atomic_type(target_type):
        raise TypeError(f"target_type must be a composite type, got {target_type.__name__}")

    # Optimization: check if any targets exist before attempting reconstruction
    has_target = False
    # Use find_instances logic to check for existence
    for _ in find_instances_inside_composite_object(obj, target_type):
        has_target = True
        break
        
    if not has_target:
        return obj

    # Perform reconstruction
    reconstructor = _ObjectReconstructor(target_type, transform_fn)
    return reconstructor.reconstruct(obj)
