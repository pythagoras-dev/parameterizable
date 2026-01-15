"""Detection utilities for Jupyter/IPython notebook environments.

Provides a function to determine whether code is running inside a
Jupyter notebook or IPython interactive shell.
"""
from __future__ import annotations

from functools import cache

__all__ = ['is_executed_in_notebook', 'reset_notebook_detection']


@cache
def is_executed_in_notebook() -> bool:
    """Return whether code is running inside a Jupyter/IPython notebook.

    Uses a lightweight heuristic: checks if IPython is present and whether the
    current shell exposes the set_custom_exc attribute, which is specific to
    IPython interactive environments (including Jupyter). The function is cached
    to avoid repeated imports and checks.

    Returns:
        bool: True if running inside a Jupyter/IPython notebook, False otherwise.
    """

    try:
        from IPython import get_ipython
        ipython = get_ipython()
        return ipython is not None and hasattr(ipython, "set_custom_exc")
    except Exception:
        return False


def reset_notebook_detection() -> None:
    """Clear the cached result of is_executed_in_notebook().

    Call this function to force re-detection of the notebook environment
    on the next call to is_executed_in_notebook(). Useful for testing
    or when the execution environment may have changed.
    """
    is_executed_in_notebook.cache_clear()