"""
"""
from __future__ import annotations

from .parameterizable_mixin import ParameterizableMixin


class SingletonMixin(ParameterizableMixin):
    """Base class for singleton classes.

    This class implements a singleton pattern where each subclass maintains
    exactly one instance that is returned on every instantiation.
    """
    _instances: dict[type, SingletonMixin] = {}

    def __new__(cls):
        """Create or return the singleton instance for the subclass.
        
        Args:
            cls: The class for which to create or retrieve the singleton instance.
            
        Returns:
            Joker: The singleton instance for the specified class.
        """
        if cls not in SingletonMixin._instances:
            SingletonMixin._instances[cls] = super().__new__(cls)
        return SingletonMixin._instances[cls]

