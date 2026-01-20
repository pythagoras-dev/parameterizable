"""Mixin for implementing the singleton pattern.

This module provides SingletonMixin, which ensures each subclass maintains
exactly one instance that is returned on every instantiation attempt. This is
useful for classes that should have only a single instance throughout the
application lifetime, such as configuration managers or resource coordinators.
"""
from __future__ import annotations

from ..mixins_and_metaclasses.parameterizable_mixin import ParameterizableMixin


class SingletonMixin(ParameterizableMixin):
    """Mixin for creating singleton classes.

    Ensures each subclass maintains exactly one instance that is returned
    on every instantiation. The singleton instance is stored per class type,
    so each subclass has its own singleton instance.

    Attributes:
        _instances: Dictionary storing the singleton instance for each class.
        _counters: Dictionary tracking the number of instantiation requests per class.

    Note:
        This implementation is not thread-safe. For multi-threaded applications,
        additional synchronization mechanisms should be added.
    """
    _instances: dict[type, SingletonMixin] = {}
    _counters: dict[type, int] = {}

    def __new__(cls, *args, **kwargs):
        """Create or return the singleton instance for this class.

        Returns:
            The singleton instance for this class.
        """
        if cls not in SingletonMixin._instances:
            SingletonMixin._instances[cls] = super().__new__(cls)
            SingletonMixin._counters[cls] = 0
        SingletonMixin._counters[cls] += 1
        return SingletonMixin._instances[cls]

