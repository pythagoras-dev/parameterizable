"""Utilities for working with Python project configuration files.

This module provides helper functions for detecting and working with
pyproject.toml files in Python projects.
"""
from pathlib import Path

from .project_analyzer import validate_path


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
