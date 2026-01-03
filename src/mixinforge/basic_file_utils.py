"""Utilities for working with Python project configuration files.

This module provides helper functions for detecting and working with
pyproject.toml files in Python projects.
"""
import shutil
from pathlib import Path


def sanitize_and_validate_path(path: Path | str, must_exist: bool = True, must_be_dir: bool = False) -> Path:
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


def folder_contains_file(folder_path: Path | str, filename: str) -> bool:
    """Check if a specific file exists in the specified folder.

    Validates the folder path and checks for the presence of a file
    with the given name in that directory.

    Args:
        folder_path: Path to the folder to check; accepts string or Path object.
        filename: Name of the file to look for in the folder.

    Returns:
        True if the file exists in the folder, False otherwise.

    Raises:
        ValueError: If folder_path is invalid or doesn't exist.
        TypeError: If folder_path is not a string or Path object.
    """
    validated_folder = sanitize_and_validate_path(folder_path, must_exist=True, must_be_dir=True)
    file_path = validated_folder / filename
    return file_path.exists() and file_path.is_file()


def folder_contains_pyproject_toml(folder_path: Path | str) -> bool:
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
    return folder_contains_file(folder_path, "pyproject.toml")


def remove_python_cache_files(folder_path: Path | str) -> tuple[int, list[str]]:
    """Remove all Python cached files from a folder and its subfolders.

    Recursively removes cache files and directories created by Python interpreter
    and popular Python tools including pytest, mypy, ruff, hypothesis, tox, and coverage.

    The following items are removed:
    - __pycache__/ directories (Python bytecode cache)
    - .pyc files (compiled Python files)
    - .pyo files (optimized compiled files, older Python versions)
    - .pytest_cache/ directories (pytest cache)
    - .ruff_cache/ directories (Ruff linter cache)
    - .mypy_cache/ directories (mypy type checker cache)
    - .hypothesis/ directories (Hypothesis test cache)
    - .tox/ directories (tox testing cache)
    - .eggs/ directories (setuptools egg cache)
    - .coverage* files (coverage data files)

    Args:
        folder_path: Path to the folder to clean; accepts string or Path object.

    Returns:
        Tuple of (count of removed items, list of removed item paths).
        Paths in the list are relative to the folder_path.

    Raises:
        ValueError: If folder_path is invalid or doesn't exist.
        TypeError: If folder_path is not a string or Path object.
    """
    validated_folder = sanitize_and_validate_path(folder_path, must_exist=True, must_be_dir=True)

    # Define patterns to remove
    cache_dirs = {'__pycache__', '.pytest_cache', '.ruff_cache', '.mypy_cache',
                  '.hypothesis', '.tox', '.eggs'}
    cache_file_extensions = {'.pyc', '.pyo'}

    removed_count = 0
    removed_items = []

    # Walk through directory tree
    # Note: When we delete a directory with shutil.rmtree(), its descendants are
    # automatically removed with it, so we won't encounter errors from trying to
    # access already-deleted nested items. Any other filesystem issues (permissions,
    # locks, etc.) are caught by the try-except block below.
    for item in validated_folder.rglob('*'):
        try:
            # Check if it's a cache directory
            if item.is_dir() and item.name in cache_dirs:
                relative_path = str(item.relative_to(validated_folder))
                removed_items.append(relative_path)
                shutil.rmtree(item)
                removed_count += 1
            # Check if it's a cache file
            elif item.is_file():
                if item.suffix in cache_file_extensions or item.name.startswith('.coverage'):
                    relative_path = str(item.relative_to(validated_folder))
                    removed_items.append(relative_path)
                    item.unlink()
                    removed_count += 1
        except (OSError, PermissionError):
            # Skip items that can't be removed
            continue

    return removed_count, removed_items
