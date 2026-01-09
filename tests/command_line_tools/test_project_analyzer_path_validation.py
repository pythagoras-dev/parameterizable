"""Tests for project_analyzer.py path validation functionality.

Tests cover path validation, security checks, and directory traversal prevention.
"""
from pathlib import Path
import pytest

from mixinforge.command_line_tools.basic_file_utils import (
    sanitize_and_validate_path,
    is_path_within_root,
)


# ============================================================================
# sanitize_and_validate_path tests
# ============================================================================

def test_sanitize_and_validate_path_with_valid_path(tmp_path):
    """Validate that a valid path is resolved correctly."""
    test_file = tmp_path / "test.py"
    test_file.write_text("# test")

    result = sanitize_and_validate_path(test_file, must_exist=True)
    assert result.exists()
    assert result.is_absolute()


def test_sanitize_and_validate_path_none_raises_valueerror():
    """Validate that None path raises ValueError."""
    with pytest.raises(ValueError, match=r"Path.*None"):
        sanitize_and_validate_path(None)


def test_sanitize_and_validate_path_empty_string_raises_valueerror():
    """Validate that empty string raises ValueError."""
    with pytest.raises(ValueError, match=r"empty"):
        sanitize_and_validate_path("")


def test_sanitize_and_validate_path_whitespace_raises_valueerror():
    """Validate that whitespace-only string raises ValueError."""
    with pytest.raises(ValueError, match=r"empty"):
        sanitize_and_validate_path("   ")


def test_sanitize_and_validate_path_invalid_type_raises_typeerror():
    """Validate that invalid type raises TypeError."""
    with pytest.raises(TypeError, match=r"string.*Path"):
        sanitize_and_validate_path(123)


def test_sanitize_and_validate_path_nonexistent_with_must_exist(tmp_path):
    """Validate that nonexistent path with must_exist=True raises ValueError."""
    nonexistent = tmp_path / "does_not_exist.py"
    with pytest.raises(ValueError, match=r"not exist"):
        sanitize_and_validate_path(nonexistent, must_exist=True)


def test_sanitize_and_validate_path_file_with_must_be_dir(tmp_path):
    """Validate that file path with must_be_dir=True raises ValueError."""
    test_file = tmp_path / "test.py"
    test_file.write_text("# test")

    with pytest.raises(ValueError, match=r"directory"):
        sanitize_and_validate_path(test_file, must_exist=True, must_be_dir=True)


def test_sanitize_and_validate_path_directory_with_must_be_dir(tmp_path):
    """Validate that directory path with must_be_dir=True succeeds."""
    result = sanitize_and_validate_path(tmp_path, must_exist=True, must_be_dir=True)
    assert result.is_dir()


def test_sanitize_and_validate_path_accepts_path_object(tmp_path):
    """Validate that Path object is accepted."""
    test_file = tmp_path / "test.py"
    test_file.write_text("# test")

    result = sanitize_and_validate_path(test_file, must_exist=True)
    assert result.exists()


def test_sanitize_and_validate_path_with_invalid_path_string():
    """Verify sanitize_and_validate_path handles OS errors gracefully."""
    # Path with null bytes should raise ValueError
    with pytest.raises(ValueError):
        sanitize_and_validate_path("\x00invalid")


def test_sanitize_and_validate_path_converts_string_to_path():
    """Verify sanitize_and_validate_path converts string to Path object."""
    result = sanitize_and_validate_path(".", must_exist=True)
    assert isinstance(result, Path)
    assert result.is_absolute()


# ============================================================================
# is_path_within_root tests
# ============================================================================

def test_is_path_within_root_true_for_subdirectory(tmp_path):
    """Verify that subdirectory is detected as within root."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    assert is_path_within_root(subdir, tmp_path) is True


def test_is_path_within_root_true_for_nested_file(tmp_path):
    """Verify that nested file is detected as within root."""
    subdir = tmp_path / "sub1" / "sub2"
    subdir.mkdir(parents=True)
    test_file = subdir / "test.py"
    test_file.write_text("# test")

    assert is_path_within_root(test_file, tmp_path) is True


def test_is_path_within_root_false_for_outside_path(tmp_path):
    """Verify that path outside root is detected correctly."""
    outside = tmp_path.parent / "outside"
    assert is_path_within_root(outside, tmp_path) is False


def test_is_path_within_root_true_for_same_path(tmp_path):
    """Verify that same path is considered within itself."""
    assert is_path_within_root(tmp_path, tmp_path) is True
