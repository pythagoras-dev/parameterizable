"""
Stack-based flattening of nested collections with cycle detection.

Avoids recursion depth limits and treats strings/bytes as atomic values.
For mappings (dicts), flattens values only (keys are ignored).
"""
from collections import deque
from collections.abc import Iterable, Iterator, Mapping
from typing import Any

from .atomics_detector import is_atomic_object

def _is_flattenable(obj: Any) -> bool:
    """Check if an object should be traversed or yielded as a leaf.

    Args:
        obj: Candidate object encountered during traversal.

    Returns:
        True to descend into obj; False to yield it as a leaf.
    """
    if is_atomic_object(obj):
        return False
    if not isinstance(obj, Iterable):
        return False
    return True


def get_atomics_from_nested_collections(obj: Iterable[Any]) -> Iterator[Any]:
    """Yield unique atomic elements from a nested collection.

    Traverses nested iterables depth-first using a stack. For mappings, only
    values are traversed. Ensures object identity uniqueness: shared
    sub-structures and duplicate atomic objects are yielded only once.

    Args:
        obj: The nested collection to flatten.

    Yields:
        Atomic (non-flattenable) elements in depth-first order.

    Raises:
        TypeError: If obj is not an Iterable.
        ValueError: If a cyclic reference is detected.
    """
    if not isinstance(obj, Iterable):
        raise TypeError(f"Expected an Iterable as input, "
                        f"got {type(obj).__name__} instead")

    root_iter = iter(obj.values()) if isinstance(obj, Mapping) else iter(obj)
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
        if _is_flattenable(item):
            if obj_id in path:
                raise ValueError(f"Cyclic reference detected at {obj_id}")
            if obj_id in seen_ids:
                continue

            seen_ids.add(obj_id)
            item_iter = iter(item.values()) if isinstance(item, Mapping) else iter(item)
            stack.append((item_iter, path | {obj_id}))
        else:
            if obj_id in seen_ids:
                continue
            seen_ids.add(obj_id)
            yield item