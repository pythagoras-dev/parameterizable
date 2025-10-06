from typing import Dict, Any


def sort_dict_by_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    """Sort a dictionary by its keys.

    Args:
        d: The dictionary to sort by keys.

    Returns:
        Dict[str, Any]: A new dictionary with the same key-value pairs,
        but with keys sorted alphabetically.

    Raises:
        AssertionError: If ``d`` is not a dictionary.
    """
    if not isinstance(d,dict):
        raise TypeError(f"d must be a dictionary, "
                        f"got {type(d).__name__} instead")
    return {k: d[k] for k in sorted(d.keys())}