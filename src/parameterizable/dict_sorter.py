from typing import Dict, Any


def sort_dict_by_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    """Sort a dictionary by its keys.

    Args:
        d (Dict[str, Any]): The dictionary to sort by keys.

    Returns:
        Dict[str, Any]: A new dictionary with the same key-value pairs,
            but with keys sorted alphabetically.
    """
    assert isinstance(d, dict)
    #return dict(sorted(d.items()))
    return {k: d[k] for k in sorted(d.keys())}