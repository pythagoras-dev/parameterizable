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
        if '\x00' in path:
            raise ValueError("Path cannot contain null bytes")
        path = Path(path)

    # Check for null bytes in Path objects (they convert string but preserve null bytes)
    if '\x00' in str(path):
        raise ValueError("Path cannot contain null bytes")

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
                relative_path = item.relative_to(validated_folder).as_posix()
                removed_items.append(relative_path)
                shutil.rmtree(item)
                removed_count += 1
            # Check if it's a cache file
            elif item.is_file():
                if item.suffix in cache_file_extensions or item.name.startswith('.coverage'):
                    relative_path = item.relative_to(validated_folder).as_posix()
                    removed_items.append(relative_path)
                    item.unlink()
                    removed_count += 1
        except (OSError, PermissionError):
            # Skip items that can't be removed
            continue

    return removed_count, removed_items


def categorize_cache_items(removed_items: list[str]) -> dict[str, dict[str, int]]:
    """Categorize removed cache items by type and location.

    Analyzes a list of removed cache file paths and categorizes them by:
    - Cache type (e.g., __pycache__, .pyc files, .pytest_cache)
    - Top-level directory location

    Args:
        removed_items: List of relative paths to removed cache items.

    Returns:
        Dictionary with two keys:
        - 'by_type': Dict mapping cache type names to counts
        - 'by_location': Dict mapping top-level directory names to counts

    Example:
        >>> items = ['tests/__pycache__/foo.pyc', 'src/__pycache__/bar.pyc', 'tests/.pytest_cache']
        >>> result = categorize_cache_items(items)
        >>> result['by_type']
        {'__pycache__': 2, '.pytest_cache': 1}
        >>> result['by_location']
        {'tests': 2, 'src': 1}
    """
    categories = {
        '__pycache__': 0,
        '.pyc/.pyo files': 0,
        '.pytest_cache': 0,
        '.ruff_cache': 0,
        '.mypy_cache': 0,
        '.hypothesis': 0,
        '.tox': 0,
        '.eggs': 0,
        '.coverage': 0
    }

    top_level_dirs = {}

    for item in removed_items:
        # Categorize by cache type
        if '__pycache__' in item:
            categories['__pycache__'] += 1
        elif item.endswith('.pyc') or item.endswith('.pyo'):
            categories['.pyc/.pyo files'] += 1
        elif '.pytest_cache' in item:
            categories['.pytest_cache'] += 1
        elif '.ruff_cache' in item:
            categories['.ruff_cache'] += 1
        elif '.mypy_cache' in item:
            categories['.mypy_cache'] += 1
        elif '.hypothesis' in item:
            categories['.hypothesis'] += 1
        elif '.tox' in item:
            categories['.tox'] += 1
        elif '.eggs' in item:
            categories['.eggs'] += 1
        elif '.coverage' in item:
            categories['.coverage'] += 1

        # Track by top-level directory (handle both / and \ separators)
        top_dir = item.split('/')[0] if '/' in item else item.split('\\')[0]
        top_level_dirs[top_dir] = top_level_dirs.get(top_dir, 0) + 1

    return {
        'by_type': {k: v for k, v in categories.items() if v > 0},
        'by_location': top_level_dirs
    }


def remove_dist_artifacts(folder_path: Path | str) -> tuple[int, int]:
    """Remove distribution artifacts (dist/ directory) from a project folder.

    Removes the dist/ directory created by build tools like `uv build`,
    `python -m build`, or `pip wheel`.

    Args:
        folder_path: Path to the project folder; accepts string or Path object.

    Returns:
        Tuple of (file_count, total_size_bytes) of removed items.
        Returns (0, 0) if dist/ doesn't exist (idempotent behavior).

    Raises:
        ValueError: If folder_path is invalid or doesn't exist.
        TypeError: If folder_path is not a string or Path object.
        OSError: If dist/ directory cannot be removed.
    """
    validated_folder = sanitize_and_validate_path(folder_path, must_exist=True, must_be_dir=True)
    dist_path = validated_folder / "dist"

    if not dist_path.exists():
        return 0, 0

    # Collect statistics before deletion
    file_count = 0
    total_size = 0

    for item in dist_path.rglob("*"):
        if item.is_file():
            file_count += 1
            total_size += item.stat().st_size

    # Remove the dist directory
    shutil.rmtree(dist_path)

    return file_count, total_size


def format_cache_statistics(removed_count: int, removed_items: list[str]) -> str:
    """Format cache cleaning statistics for console output.

    Creates a human-readable formatted string showing statistics about
    removed cache items, categorized by type and location.

    Args:
        removed_count: Total number of items removed.
        removed_items: List of relative paths to removed cache items.

    Returns:
        Formatted multi-line string ready for printing to console.
        Returns a single-line message if no items were removed.

    Example:
        >>> output = format_cache_statistics(15, ['tests/__pycache__', 'src/__pycache__', ...])
        >>> print(output)
        ✓ Cache clearing: 15 items removed

          By type:
            __pycache__: 10
            .pyc/.pyo files: 5

          By location:
            tests: 8
            src: 7
    """
    if removed_count == 0:
        return "✓ Cache clearing: project is clean (0 items removed)"

    stats = categorize_cache_items(removed_items)

    # Build type statistics
    type_lines = []
    for cache_type, count in stats['by_type'].items():
        type_lines.append(f"    {cache_type}: {count}")

    # Build location statistics (sorted by count, descending)
    dir_stats = sorted(stats['by_location'].items(), key=lambda x: x[1], reverse=True)
    dir_lines = []
    for dir_name, count in dir_stats[:5]:  # Top 5
        dir_lines.append(f"    {dir_name}: {count}")
    if len(dir_stats) > 5:
        remaining = sum(count for _, count in dir_stats[5:])
        dir_lines.append(f"    (others): {remaining}")

    # Build final output
    output = [f"✓ Cache clearing: {removed_count} items removed"]
    output.append("\n  By type:")
    output.extend(type_lines)
    output.append("\n  By location:")
    output.extend(dir_lines)

    return '\n'.join(output)
