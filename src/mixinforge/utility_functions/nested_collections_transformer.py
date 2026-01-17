"""Reconstruction and transformation of nested composite objects.

Provides functionality to transform specific instances within deeply nested
structures while preserving the overall object graph and handling cycles.
"""
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, Callable
from typing import Any, TypeVar
from dataclasses import replace, fields
from itertools import islice

from ..utility_functions.atomics_detector import is_atomic_object, is_atomic_type
from .nested_collections_inspector import (
    _is_standard_mapping,
    _is_standard_iterable,
    _yield_attributes,
    find_instances_inside_composite_object
)

T = TypeVar('T')

# ==============================================================================
# Internal helpers
# ==============================================================================
def _safe_recreate_container(original_type: type, items: Iterable[Any]) -> Any:
    """Best-effort reconstruction that won't explode for exotic containers."""
    try:
        return original_type(items)
    except Exception:
        if issubclass(original_type, tuple):
            return tuple(items)
        if issubclass(original_type, set):
            return set(items)
        return list(items)


def _copy_instance_attributes(source: Any, target: Any) -> None:
    """Copy instance attributes from source to target via __dict__."""
    if hasattr(source, '__dict__'):
        for attr, val in source.__dict__.items():
            setattr(target, attr, val)


def _create_dict_subclass_copy(original: dict) -> dict:
    """Create a copy of a dict subclass, bypassing __init__ and copying attributes."""
    original_type = type(original)
    result = original_type.__new__(original_type)
    dict.update(result, original)
    _copy_instance_attributes(original, result)
    return result


# ==============================================================================
# Reconstruction Logic
# ==============================================================================

class _ObjectReconstructor:
    """Helper class for recursive object reconstruction with cycle handling."""
    
    def __init__(self, target_type: type[Any], transform_fn: Callable[[Any], Any]):
        self.target_type = target_type
        self.transform_fn = transform_fn
        self.seen_ids: dict[int, Any] = {}

    def reconstruct(self, original: Any) -> Any:
        """Reconstruct an object, replacing transformed children."""
        obj_id = id(original)

        # If we've already reconstructed this object, return it
        if obj_id in self.seen_ids:
            return self.seen_ids[obj_id]

        # Atomic objects don't need reconstruction
        if is_atomic_object(original):
            self.seen_ids[obj_id] = original
            return original

        match original:
            case _ if isinstance(original, self.target_type):
                return self._reconstruct_target_type(original, obj_id)

            case _ if _is_standard_mapping(original):
                return self._reconstruct_standard_mapping(original, obj_id)

            case _ if _is_standard_iterable(original):
                return self._reconstruct_standard_iterable(original, obj_id)

            case Mapping():
                return self._reconstruct_generic_mapping(original, obj_id)

            case Iterable():
                return self._reconstruct_generic_iterable(original, obj_id)

            case _:
                return self._reconstruct_custom_object(original, obj_id)

    def _reconstruct_mapping_items(self, original: Mapping) -> tuple[bool, list[tuple[Any, Any]]]:
        """Reconstruct all key-value pairs, returning (changed, new_items)."""
        changed = False
        new_items = []
        for k, v in original.items():
            new_k = self.reconstruct(k)
            new_v = self.reconstruct(v)
            if new_k is not k or new_v is not v:
                changed = True
            new_items.append((new_k, new_v))
        return changed, new_items

    def _reconstruct_iterable_items(self, original: Iterable) -> tuple[bool, list[Any]]:
        """Reconstruct all items, returning (changed, new_items)."""
        changed = False
        new_items = []
        for item in original:
            new_item = self.reconstruct(item)
            if new_item is not item:
                changed = True
            new_items.append(new_item)
        return changed, new_items

    def _reconstruct_target_type(self, original: Any, obj_id: int) -> Any:
        # Mark as being processed to prevent infinite recursion
        self.seen_ids[obj_id] = original  # Temporary placeholder

        # Apply the transformation first
        transformed = self.transform_fn(original)

        # Now recursively process the transformed object's children
        transformed_reconstructed = self._reconstruct_object_attributes(transformed)

        self.seen_ids[obj_id] = transformed_reconstructed
        return transformed_reconstructed

    def _reconstruct_standard_mapping(self, original: Any, obj_id: int) -> Any:
        # Create empty result container, handling defaultdict specially
        if isinstance(original, defaultdict):
            if type(original) is defaultdict:
                result = defaultdict(original.default_factory)
            else:
                result = type(original).__new__(type(original))
                defaultdict.__init__(result, original.default_factory)
                _copy_instance_attributes(original, result)
        else:
            result = type(original)()
        self.seen_ids[obj_id] = result

        changed, new_items = self._reconstruct_mapping_items(original)

        if not changed:
            self.seen_ids[obj_id] = original
            return original

        for k, v in new_items:
            result[k] = v
        return result

    def _reconstruct_standard_iterable(self, original: Any, obj_id: int) -> Any:
        if isinstance(original, list):
            # Mutable: create placeholder for cycle handling, then fill
            result = []
            self.seen_ids[obj_id] = result
            changed, new_items = self._reconstruct_iterable_items(original)

            if not changed:
                self.seen_ids[obj_id] = original
                return original

            result.extend(new_items)
            return result
        else:
            # Immutable: use placeholder, reconstruct after
            self.seen_ids[obj_id] = original
            changed, new_items = self._reconstruct_iterable_items(original)

            if not changed:
                return original

            result = _safe_recreate_container(type(original), new_items)
            self.seen_ids[obj_id] = result
            return result

    def _reconstruct_generic_mapping(self, original: Mapping, obj_id: int) -> Any:
        changed, new_items = self._reconstruct_mapping_items(original)

        if not changed:
            self.seen_ids[obj_id] = original
            return original

        new_dict = dict(new_items)
        if isinstance(original, dict):
            # For dict subclasses, bypass __init__ and copy attributes
            result = _create_dict_subclass_copy(original)
            result.clear()
            result.update(new_dict)
        else:
            result = _safe_recreate_container(type(original), new_dict.items())

        self.seen_ids[obj_id] = result
        return result

    def _reconstruct_generic_iterable(self, original: Iterable, obj_id: int) -> Any:
        changed, new_items = self._reconstruct_iterable_items(original)

        if not changed:
            self.seen_ids[obj_id] = original
            return original

        result = _safe_recreate_container(type(original), new_items)
        self.seen_ids[obj_id] = result
        return result

    def _reconstruct_custom_object(self, original: Any, obj_id: int) -> Any:
        result = self._reconstruct_object_attributes(original)
        self.seen_ids[obj_id] = result
        return result

    def _reconstruct_object_attributes(self, obj_to_process: Any) -> Any:
        """Reconstruct an object's attributes, replacing any target instances."""
        if is_atomic_object(obj_to_process):
            return obj_to_process

        # For dataclass or regular objects with __dict__ or __slots__
        if hasattr(obj_to_process, '__dict__') or hasattr(obj_to_process.__class__, '__slots__'):
            children_list = list(_yield_attributes(obj_to_process))

            new_children = []
            changed = False
            for child in children_list:
                new_child = self.reconstruct(child)
                new_children.append(new_child)
                if new_child is not child:
                    changed = True

            if not changed:
                return obj_to_process

            # Try to create a new instance with transformed attributes
            if hasattr(obj_to_process, '__dataclass_fields__'):
                field_values = {}
                field_list = fields(obj_to_process)
                for field, new_value in zip(field_list, new_children):
                    field_values[field.name] = new_value
                return replace(obj_to_process, **field_values)
            else:
                # Create a new instance for regular objects (with __dict__ or __slots__)
                new_obj = object.__new__(type(obj_to_process))

                # Get attribute names from __dict__ and/or __slots__
                attr_names = []
                if hasattr(obj_to_process, '__dict__'):
                    attr_names.extend(obj_to_process.__dict__.keys())
                if hasattr(obj_to_process.__class__, '__slots__'):
                    # Get all slots including inherited ones
                    from .nested_collections_inspector import _get_all_slots
                    slots = _get_all_slots(type(obj_to_process))
                    for slot in slots:
                        if hasattr(obj_to_process, slot):
                            attr_names.append(slot)

                # Set the transformed attributes on the new object
                for attr_name, new_value in zip(attr_names, new_children):
                    setattr(new_obj, attr_name, new_value)

                return new_obj

        return obj_to_process


def transform_instances_inside_composite_object(
    obj: Any,
    target_type: type[T],
    transform_fn: Callable[[T], Any]
) -> Any:
    """Transform all instances of a target type within any object.

    Performs traversal of iterables, mappings, and custom objects
    (via __dict__ and __slots__). Transforms all instances of target_type
    using transform_fn and reconstructs the composite object with the
    transformed instances.

    If no instances of target_type are found, returns the original object
    unchanged.

    Handles cycles gracefully: each object is transformed only once, and
    cycle structure is preserved in the result.

    Mapping keys and values are both traversed and can be transformed.

    Args:
        obj: The object to search within and transform.
        target_type: The composite type to search for and transform.
        transform_fn: Function to apply to each instance of target_type.

    Returns:
        The transformed composite object, or the original if no matches found.

    Raises:
        TypeError: If target_type is atomic.
    """

    if is_atomic_type(target_type):
        raise TypeError(f"target_type must be a composite type, got {target_type.__name__}")

    # If obj is an iterator, convert to list to prevent consumption during probe
    if isinstance(obj, Iterator):
        obj = list(obj)

    # Optimization: check if any targets exist before attempting reconstruction
    probe = find_instances_inside_composite_object(obj, target_type)
    if not any(True for _ in islice(probe, 1)):
        return obj

    reconstructor = _ObjectReconstructor(target_type, transform_fn)
    return reconstructor.reconstruct(obj)
