"""
Stack-based flattening of nested iterables with cycle detection.

Avoids recursion depth limits and treats strings/bytes as atomic values.
"""
from collections.abc import Iterable
from typing import Any, Iterator
from collections import deque

# Types treated as atomic (not recursively flattened).
# Strings/bytes are iterable but should not be decomposed into characters/bytes.
_ATOMIC_TYPES = (str, bytes, bytearray, memoryview
    , int, float, complex, bool, type(None))


def _is_flattenable(obj: Any) -> bool:
    """
    Check if an object should be recursively flattened.

    Parameters
    ----------
    obj : Any
        The object to check.

    Returns
    -------
    bool
        True for iterables (list, tuple, set, etc.), False for atomic types
        (str, bytes, numbers, None).

    Examples
    --------
    >>> _is_flattenable([1, 2, 3])
    True
    >>> _is_flattenable("hello")
    False
    """
    if isinstance(obj, _ATOMIC_TYPES):
        return False
    else:
        return isinstance(obj, Iterable)


def flatten_iterative(nested_iterable: Iterable[Any]) -> Iterator[Any]:
    """
    Flatten nested iterables using stack-based depth-first traversal.

    Accepts any iterable (lists, tuples, sets, generators, numpy arrays, etc.).
    Treats only true iterables (excluding str/bytes) as containers.
    Detects cycles to avoid infinite loops.

    Parameters
    ----------
    nested_iterable : Iterable[Any]
        The possibly nested iterable to flatten.

    Yields
    ------
    Any
        Atomic elements in depth-first left-to-right order.

    Raises
    ------
    TypeError
        If *nested_iterable* is not an iterable.
    ValueError
        For cyclic structures.

    Examples
    --------
    >>> list(flatten_iterative([1, (2, {3, 4}), 5]))
    [1, 2, 3, 4, 5]
    >>> list(flatten_iterative([[["a"], "b"], "c"]))
    ['a', 'b', 'c']
    """
    if not isinstance(nested_iterable, Iterable):
        raise TypeError(
            f"Expected an iterable, got {type(nested_iterable).__name__}"
        )

    # Stack stores (iterator, ancestor_ids) tuples for cycle detection.
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
            # Copy-on-write: path | {obj_id} creates new set without mutating parent's path
            stack.append((iter(item), path | {obj_id}))
        else:
            yield item