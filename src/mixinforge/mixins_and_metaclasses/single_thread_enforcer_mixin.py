"""Single-thread execution enforcement with multi-process support.

This module provides utilities to ensure that code runs only on the thread
that first initialized it, while automatically supporting process-based
parallelism through fork detection. After a fork, the child process
automatically becomes the new owner thread for that process.
"""

from __future__ import annotations

import inspect
import os
import threading

_owner_thread_native_id: int | None = None
_owner_thread_name: str | None = None
_owner_process_id: int | None = None


def _restrict_to_single_thread() -> None:
    """Ensure current thread is the original thread.

    Validates that the calling thread is the same thread that first initialized
    the program. Automatically resets ownership after process forks to
    support multi-process parallelism.

    Raises:
        RuntimeError: If called from a different thread than the owner thread.
    """
    global _owner_thread_native_id, _owner_thread_name, _owner_process_id

    current_process_id = os.getpid()
    current_thread_native_id = threading.get_native_id()
    current_thread_name = threading.current_thread().name

    if _owner_process_id is not None and current_process_id != _owner_process_id:
        _owner_thread_native_id = None
        _owner_thread_name = None
        _owner_process_id = None

    if _owner_thread_native_id is None:
        _owner_thread_native_id = current_thread_native_id
        _owner_thread_name = current_thread_name
        _owner_process_id = current_process_id
        return

    if current_thread_native_id != _owner_thread_native_id:
        caller = inspect.stack()[1]
        raise RuntimeError(
            "This object is restricted to single-threaded execution.\n"
            f"Owner thread : {_owner_thread_native_id} ({_owner_thread_name})\n"
            f"Current thread: {current_thread_native_id} ({current_thread_name}) at "
            f"{caller.filename}:{caller.lineno}\n"
            "For parallelism, use multi-process execution.")


def _reset_thread_ownership() -> None:
    """Reset thread ownership tracking.

    Note:
        This function is intended for testing purposes only.
    """
    global _owner_thread_native_id, _owner_thread_name, _owner_process_id
    _owner_thread_native_id = None
    _owner_thread_name = None
    _owner_process_id = None


class SingleThreadEnforcerMixin:
    """Mixin to enforce single-threaded execution with multi-process support.

    Add this mixin to any class to ensure its methods are called only from
    the thread that first instantiated it. Automatically resets ownership
    after process forks to support multi-process parallelism while preventing
    concurrent threading issues.

    The enforcement happens at instantiation and can be manually triggered
    via the _restrict_to_single_thread method.

    Raises:
        RuntimeError: If instantiated or if _restrict_to_single_thread is called
            from a different thread than the owner thread.

    Example:
        >>> class MyClass(SingleThreadEnforcerMixin):
        ...     def process(self):
        ...         self._restrict_to_single_thread()
        ...         # Process safely on owner thread
    """

    def _restrict_to_single_thread(self):
        """Validate that the current thread is the owner thread.

        Raises:
            RuntimeError: If called from a different thread than the owner thread.
        """
        _restrict_to_single_thread()

    def __init__(self, *args, **kwargs):
        """Initialize and register the current thread as the owner."""
        super().__init__(*args, **kwargs)
        _restrict_to_single_thread()