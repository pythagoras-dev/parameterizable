"""Context manager to suppress stdout and stderr output.

Redirects stdout and stderr to the system null device (os.devnull).
Useful for silencing noisy operations in background processes or tests.
"""

import os
from contextlib import ExitStack, redirect_stderr, redirect_stdout


__all__ = ["OutputSuppressor"]


class OutputSuppressor:
    """Context manager to suppress stdout and stderr.

    Example:
        with OutputSuppressor():
            noisy_function()  # Output is discarded

    Notes:
        Internally uses contextlib.ExitStack to manage all redirections and to
        ensure restoration even when exceptions are raised.
    """

    def __enter__(self):
        """Enter the suppression context.

        Returns:
            OutputSuppressor: The context manager instance.
        """
        self._stack = ExitStack()
        devnull = self._stack.enter_context(open(os.devnull, "w"))
        self._stack.enter_context(redirect_stdout(devnull))
        self._stack.enter_context(redirect_stderr(devnull))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the suppression context, restoring stdio streams.

        Args:
            exc_type: Exception class if an exception occurred, else None.
            exc_val: Exception instance if an exception occurred, else None.
            exc_tb: Traceback if an exception occurred, else None.

        Returns:
            bool: Whatever is returned by ExitStack.__exit__().
        """
        return self._stack.__exit__(exc_type, exc_val, exc_tb)
