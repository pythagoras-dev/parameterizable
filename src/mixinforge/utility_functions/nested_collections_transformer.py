"""Reconstruction and transformation of nested composite objects.

Provides functionality to transform specific instances within deeply nested
structures while preserving the overall object graph and handling cycles.
"""
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, Callable
from typing import Any, TypeVar
from dataclasses import replace, fields

from ..utility_functions.atomics_detector import is_atomic_object
from .nested_collections_inspector import (
    _is_standard_mapping,
    _is_standard_iterable,
    ClassInfo,
    _is_valid_classinfo,
)

T = TypeVar('T')

# ==============================================================================
# Internal helpers
# ==============================================================================
def _safe_recreate_container(original_type: type, items: Iterable[Any], *, original: Any = None) -> Any:
    """Best-effort reconstruction that won't explode for exotic containers.

    Args:
        original_type: The type to recreate.
        items: The items to populate the container with.
        original: Optional original object, used to preserve special attributes
            like defaultdict.default_factory.
    """
    try:
        # Preserve defaultdict.default_factory if applicable
        if issubclass(original_type, defaultdict):
            factory = original.default_factory if original is not None else None
            result = defaultdict(factory, items)
            # For subclasses, we need to create the proper type
            if original_type is not defaultdict:
                subclass_result = original_type.__new__(original_type)
                defaultdict.__init__(subclass_result, factory)
                subclass_result.update(result)
                if original is not None:
                    _copy_instance_attributes(original, subclass_result)
                return subclass_result
            return result
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

    def __init__(self, classinfo: ClassInfo, transform_fn: Callable[[Any], Any], deep_transformation: bool = True):
        self.classinfo = classinfo
        self.transform_fn = transform_fn
        self.deep_transformation = deep_transformation
        self.seen_ids: dict[int, Any] = {}
        self.any_replacements: bool = False

    def reconstruct(self, original: Any) -> Any:
        """Reconstruct an object, replacing transformed children."""
        obj_id = id(original)

        # If we've already reconstructed this object, return it
        if obj_id in self.seen_ids:
            return self.seen_ids[obj_id]

        # Check if this is a target instance BEFORE the atomic early-return
        if isinstance(original, self.classinfo):
            return self._reconstruct_target_type(original, obj_id)

        # Atomic objects don't need reconstruction (and aren't targets at this point)
        if is_atomic_object(original):
            self.seen_ids[obj_id] = original
            return original

        match original:
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
        self.any_replacements = True

        # Apply the transformation first
        transformed = self.transform_fn(original)

        # Only recursively process the transformed object's children if deep_transformation is True
        if self.deep_transformation:
            transformed_reconstructed = self._reconstruct_object_attributes(transformed)
        else:
            transformed_reconstructed = transformed

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
            result = _safe_recreate_container(type(original), new_dict.items(), original=original)

        self.seen_ids[obj_id] = result
        return result

    def _reconstruct_generic_iterable(self, original: Iterable, obj_id: int) -> Any:
        # Iterator subclasses rebuilt via constructor will re-consume items.
        # Convert to list first to avoid re-consumption issues.
        if isinstance(original, Iterator):
            original = list(original)

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
            # Handle dataclasses by field name to avoid ordering assumptions
            if hasattr(obj_to_process, '__dataclass_fields__'):
                field_values = {}
                changed = False
                for field in fields(obj_to_process):
                    original_value = getattr(obj_to_process, field.name)
                    new_value = self.reconstruct(original_value)
                    if new_value is not original_value:
                        changed = True
                    field_values[field.name] = new_value

                if not changed:
                    return obj_to_process
                return replace(obj_to_process, **field_values)
            else:
                # Regular objects with __dict__ or __slots__
                # Collect attribute names from __dict__ and/or __slots__
                attr_names = []
                if hasattr(obj_to_process, '__dict__'):
                    attr_names.extend(obj_to_process.__dict__.keys())
                if hasattr(obj_to_process.__class__, '__slots__'):
                    from .nested_collections_inspector import _get_all_slots
                    slots = _get_all_slots(type(obj_to_process))
                    for slot in slots:
                        if hasattr(obj_to_process, slot):
                            attr_names.append(slot)

                # Reconstruct attributes by name
                new_values = {}
                changed = False
                for attr_name in attr_names:
                    original_value = getattr(obj_to_process, attr_name)
                    new_value = self.reconstruct(original_value)
                    if new_value is not original_value:
                        changed = True
                    new_values[attr_name] = new_value

                if not changed:
                    return obj_to_process

                # Create a new instance and set transformed attributes
                new_obj = object.__new__(type(obj_to_process))
                for attr_name, new_value in new_values.items():
                    setattr(new_obj, attr_name, new_value)

                return new_obj

        return obj_to_process


def transform_instances_inside_composite_object(
    obj: Any,
    classinfo: ClassInfo,
    transform_fn: Callable[[Any], Any],
    deep_transformation: bool = True
) -> Any:
    """Transform all instances of a target type within any object.

    Performs traversal of iterables, mappings, and custom objects
    (via __dict__ and __slots__). Transforms all instances matching classinfo
    using transform_fn and reconstructs the composite object with the
    transformed instances.

    If no matching instances are found, returns the original object unchanged.

    Handles cycles gracefully: each object is transformed only once, and
    cycle structure is preserved in the result.

    Mapping keys and values are both traversed and can be transformed.

    Args:
        obj: The object to search within and transform.
        classinfo: Type or tuple of types to search for and transform. Accepts
            the same values as the second argument to isinstance(): a single
            type, a tuple of types (recursively), or a union type (e.g., int | str).
        transform_fn: Function to apply to each matching instance.
            Should be idempotent (return the same result for the same input)
            since objects are deduplicated by identity and the function is
            called only once per unique object.
        deep_transformation: If True (default), after transforming an instance,
            continue recursively processing its children for more matching
            instances. If False, stop traversal at transformed instances.

    Returns:
        The transformed composite object, or the original if no matches found.
    """

    if not _is_valid_classinfo(classinfo):
        raise TypeError(
            f"classinfo must be a type, tuple of types, or union type, "
            f"got {type(classinfo).__name__}"
        )


    if not callable(transform_fn):
        raise TypeError(f"transform_fn must be callable, got {type(transform_fn).__name__}")

    # If obj is an iterator, convert to list to allow traversal
    if isinstance(obj, Iterator):
        obj = list(obj)

    reconstructor = _ObjectReconstructor(classinfo, transform_fn, deep_transformation)
    result = reconstructor.reconstruct(obj)
    return result if reconstructor.any_replacements else obj
