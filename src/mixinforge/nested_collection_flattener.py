"""
Stack-based flattening of nested collections with cycle detection.

Avoids recursion depth limits and treats strings/bytes as atomic values.
For mappings (dicts), flattens values only (keys are ignored).
"""
from collections.abc import Iterable, Mapping
from typing import Any, Iterator
from collections import deque

from .atomics_detector import is_atomic_object

def _is_flattenable(obj: Any) -> bool:
    """Return True when *obj* should be traversed further.

    The predicate combines three rules:

    1. Objects whose **type** is registered as atomic via
       ``mixinforge.atomics_detector.is_atomic_object`` are *not*
       flattenable.
    2. Anything that is **not** an ``Iterable`` is obviously atomic.
    3. Certain pathological “self-iterating” sentinels (``iter(obj) is obj``)
       are treated as atomic to avoid infinite loops.

    Parameters
    ----------
    obj:
        Candidate object encountered during the walk.

    Returns
    -------
    bool
        ``True`` → descend into *obj*;
        ``False`` → yield *obj* as a leaf value.
    """
    # Rule 1 – explicit atomic registration wins immediately
    if is_atomic_object(obj):
        return False

    # Rule 2 – only genuine iterables can be flattened
    if not isinstance(obj, Iterable):
        return False

    # Rule 3 – guard against iterables that return themselves from __iter__
    # (e.g. Python’s sentinel objects or intentionally buggy classes)
    if iter(obj) is obj:
        return False

    # Otherwise the object looks safe to traverse
    return True


def flatten_nested_collections(nested_iterable: Iterable[Any]) -> Iterator[Any]:
    """Flatten nested collections using stack-based depth-first traversal.

    Accepts any iterable (lists, tuples, sets, generators, numpy arrays, etc.).
    Treats only true iterables (excluding str/bytes/arrays) as containers.
    For mappings (dicts), flattens values only; keys are ignored.
    Detects cycles to avoid infinite loops.

    Args:
        nested_iterable: The possibly nested collection to flatten.

    Yields:
        Atomic elements in depth-first left-to-right order.

    Raises:
        TypeError: If nested_iterable is not an iterable.
        ValueError: For cyclic structures.

    Example:
        >>> list(flatten_nested_collections([1, (2, {3, 4}), 5]))
        [1, 2, 3, 4, 5]
        >>> list(flatten_nested_collections([[["a"], "b"], "c"]))
        ['a', 'b', 'c']
        >>> list(flatten_nested_collections([1, {"x": [2, 3], "y": 4}, 5]))
        [1, 2, 3, 4, 5]
        >>> list(flatten_nested_collections({"a": 1, "b": [2, 3]}))
        [1, 2, 3]
    """
    if not isinstance(nested_iterable, Iterable):
        raise TypeError(
            f"Expected an iterable, got {type(nested_iterable).__name__}"
        )

    # Stack stores (iterator, ancestor_ids) tuples for cycle detection.
    root_iter: Iterator[Any]
    if isinstance(nested_iterable, Mapping):
        root_iter = iter(nested_iterable.values())
    else:
        root_iter = iter(nested_iterable)
    root_id = id(nested_iterable)
    stack: deque[tuple[Iterator[Any], set[int]]] = deque([(root_iter, {root_id})])

    while stack:
        it, path = stack[-1]

        try:
            item = next(it)
        except StopIteration:
            stack.pop()
            continue

        if _is_flattenable(item):
            obj_id = id(item)
            if obj_id in path:
                raise ValueError("Cyclic reference detected")
            # For mappings, iterate over values only (keys are ignored).
            item_iter = iter(item.values()) if isinstance(item, Mapping) else iter(item)
            # Copy-on-write: path | {obj_id} creates new set without mutating parent's path
            stack.append((item_iter, path | {obj_id}))
        else:
            yield item