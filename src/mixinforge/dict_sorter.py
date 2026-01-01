from typing import Dict, Any


def sort_dict_by_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return a new dictionary with keys sorted alphabetically.

    Args:
        d: The input mapping to sort by keys.

    Returns:
        Dict[str, Any]: A new dictionary containing the same key-value pairs as
        ``d``, but with keys in ascending alphabetical order.

    Raises:
        TypeError: If ``d`` is not a dictionary.
    """
    if not isinstance(d, dict):
        raise TypeError(
            f"d must be a dictionary, got {type(d).__name__} instead"
        )
    return {k: d[k] for k in sorted(d.keys())}