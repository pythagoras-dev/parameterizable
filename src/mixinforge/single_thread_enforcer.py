"""Single-thread code execution enforcement.

"""

from __future__ import annotations

import inspect
import os
import threading

_portal_native_id: int | None = None
_portal_thread_name: str | None = None
_owner_pid: int | None = None


def ensure_single_thread() -> None:
    """Ensure current thread is the original thread.

    Validates that the calling thread is the same thread that first initialized
    the program. Automatically resets ownership after process forks to
    support multi-process parallelism.

    Raises:
        RuntimeError: If called from a different thread than the owner thread.
    """
    global _portal_native_id, _portal_thread_name, _owner_pid

    curr_pid = os.getpid()
    curr_native_id = threading.get_native_id()
    curr_name = threading.current_thread().name

    if _owner_pid is not None and curr_pid != _owner_pid:
        _portal_native_id = None
        _portal_thread_name = None
        _owner_pid = None

    if _portal_native_id is None:
        _portal_native_id = curr_native_id
        _portal_thread_name = curr_name
        _owner_pid = curr_pid
        return

    if curr_native_id != _portal_native_id:
        caller = inspect.stack()[1]
        raise RuntimeError(
            "Pythagoras portals are single-threaded by design.\n"
            f"Owner thread : {_portal_native_id} ({_portal_thread_name})\n"
            f"Current thread: {curr_native_id} ({curr_name}) at "
            f"{caller.filename}:{caller.lineno}\n"
            "For parallelism use swarming (multi-process).")


def _reset_single_thread_enforcer() -> None:
    """Reset the thread ownership for the current process.

    For unit tests only.
    """
    global _portal_native_id, _portal_thread_name, _owner_pid
    _portal_native_id = None
    _portal_thread_name = None
    _owner_pid = None