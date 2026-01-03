"""Utilities for working with Python project configuration files.

This module provides helper functions for detecting and working with
pyproject.toml files in Python projects.
"""
from pathlib import Path


def validate_path(path: Path | str, must_exist: bool = True, must_be_dir: bool = False) -> Path:
    """Validate and sanitize a file path for secure access.

    Ensures the path is valid, resolves it to an absolute normalized form,
    and checks for path traversal attempts. This prevents directory traversal
    vulnerabilities and ensures consistent path handling.

    Args:
        path: Path to validate; accepts string or Path object.
        must_exist: Whether the path must exist on the filesystem.
        must_be_dir: Whether the path must be a directory (if it exists).

    Returns:
        Resolved absolute Path object with normalized components.

    Raises:
        ValueError: If path is None, empty, invalid, doesn't exist when required,
            or contains suspicious patterns.
        TypeError: If path is not a string or Path object.
    """
    if path is None:
        raise ValueError("Path cannot be None")

    if not isinstance(path, (str, Path)):
        raise TypeError(f"Path must be a string or Path object, got {type(path)}")

    if isinstance(path, str):
        if not path.strip():
            raise ValueError("Path cannot be empty or whitespace")
        path = Path(path)

    try:
        resolved_path = path.resolve()
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid path: {e}")

    if must_exist and not resolved_path.exists():
        raise ValueError(f"Path does not exist: {resolved_path}")

    if must_be_dir and resolved_path.exists() and not resolved_path.is_dir():
        raise ValueError(f"Path is not a directory: {resolved_path}")

    return resolved_path


def is_path_within_root(file_path: Path, root_path: Path) -> bool:
    """Check if a file path is within the root directory.

    Prevents directory traversal by verifying that the resolved file path
    is a descendant of the root path.

    Args:
        file_path: Path to check for containment.
        root_path: Root directory that should contain the file.

    Returns:
        True if file_path is within root_path, False otherwise.
    """
    try:
        file_path.resolve().relative_to(root_path.resolve())
        return True
    except ValueError:
        return False


def has_pyproject_toml(folder_path: Path | str) -> bool:
    """Check if a pyproject.toml file exists in the specified folder.

    Validates the folder path and checks for the presence of a pyproject.toml
    file in that directory.

    Args:
        folder_path: Path to the folder to check; accepts string or Path object.

    Returns:
        True if pyproject.toml exists in the folder, False otherwise.

    Raises:
        ValueError: If folder_path is invalid or doesn't exist.
        TypeError: If folder_path is not a string or Path object.
    """
    validated_folder = validate_path(folder_path, must_exist=True, must_be_dir=True)
    pyproject_path = validated_folder / "pyproject.toml"
    return pyproject_path.exists() and pyproject_path.is_file()
