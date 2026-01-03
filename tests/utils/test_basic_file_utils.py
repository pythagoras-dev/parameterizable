"""Tests for basic_file_utils.py functionality.

Tests cover detection of pyproject.toml files in project directories,
including path validation and error handling.
"""
from pathlib import Path
import pytest

from mixinforge.basic_file_utils import folder_contains_pyproject_toml


# ============================================================================
# folder_contains_pyproject_toml tests - Positive cases
# ============================================================================

def test_has_pyproject_toml_returns_true_when_file_exists(tmp_path):
    """Verify that folder_contains_pyproject_toml returns True when pyproject.toml exists."""
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text("[project]\nname = 'test'\n")

    assert folder_contains_pyproject_toml(tmp_path) is True


def test_has_pyproject_toml_accepts_string_path(tmp_path):
    """Verify that folder_contains_pyproject_toml accepts string path."""
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text("[project]\nname = 'test'\n")

    assert folder_contains_pyproject_toml(str(tmp_path)) is True


def test_has_pyproject_toml_accepts_path_object(tmp_path):
    """Verify that folder_contains_pyproject_toml accepts Path object."""
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text("[project]\nname = 'test'\n")

    assert folder_contains_pyproject_toml(tmp_path) is True


# ============================================================================
# folder_contains_pyproject_toml tests - Negative cases
# ============================================================================

def test_has_pyproject_toml_returns_false_when_file_missing(tmp_path):
    """Verify that folder_contains_pyproject_toml returns False when pyproject.toml doesn't exist."""
    # tmp_path exists but has no pyproject.toml
    assert folder_contains_pyproject_toml(tmp_path) is False


def test_has_pyproject_toml_returns_false_when_other_files_exist(tmp_path):
    """Verify that folder_contains_pyproject_toml returns False even when other files exist."""
    # Create other files but not pyproject.toml
    (tmp_path / "setup.py").write_text("# setup")
    (tmp_path / "README.md").write_text("# README")

    assert folder_contains_pyproject_toml(tmp_path) is False


def test_has_pyproject_toml_raises_on_none_path():
    """Verify that folder_contains_pyproject_toml raises ValueError for None path."""
    with pytest.raises(ValueError, match="Path cannot be None"):
        folder_contains_pyproject_toml(None)


def test_has_pyproject_toml_raises_on_empty_string():
    """Verify that folder_contains_pyproject_toml raises ValueError for empty string."""
    with pytest.raises(ValueError, match="cannot be empty"):
        folder_contains_pyproject_toml("")


def test_has_pyproject_toml_raises_on_whitespace_string():
    """Verify that folder_contains_pyproject_toml raises ValueError for whitespace string."""
    with pytest.raises(ValueError, match="cannot be empty"):
        folder_contains_pyproject_toml("   ")


def test_has_pyproject_toml_raises_on_invalid_type():
    """Verify that folder_contains_pyproject_toml raises TypeError for invalid type."""
    with pytest.raises(TypeError, match="must be a string or Path"):
        folder_contains_pyproject_toml(123)


def test_has_pyproject_toml_raises_on_nonexistent_folder(tmp_path):
    """Verify that folder_contains_pyproject_toml raises ValueError for nonexistent folder."""
    nonexistent = tmp_path / "does_not_exist"

    with pytest.raises(ValueError, match="does not exist"):
        folder_contains_pyproject_toml(nonexistent)


def test_has_pyproject_toml_raises_on_file_path(tmp_path):
    """Verify that folder_contains_pyproject_toml raises ValueError when path is a file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    with pytest.raises(ValueError, match="not a directory"):
        folder_contains_pyproject_toml(test_file)


# ============================================================================
# folder_contains_pyproject_toml tests - Edge cases
# ============================================================================

def test_has_pyproject_toml_returns_false_when_pyproject_is_directory(tmp_path):
    """Verify that folder_contains_pyproject_toml returns False when pyproject.toml is a directory."""
    # Create pyproject.toml as a directory instead of a file
    pyproject_dir = tmp_path / "pyproject.toml"
    pyproject_dir.mkdir()

    assert folder_contains_pyproject_toml(tmp_path) is False


def test_has_pyproject_toml_in_nested_project(tmp_path):
    """Verify that folder_contains_pyproject_toml only checks the specified directory."""
    # Create nested structure
    nested = tmp_path / "nested" / "project"
    nested.mkdir(parents=True)

    # Put pyproject.toml in nested directory
    (nested / "pyproject.toml").write_text("[project]\nname = 'nested'\n")

    # Should return False for tmp_path (no pyproject.toml there)
    assert folder_contains_pyproject_toml(tmp_path) is False

    # Should return True for nested directory
    assert folder_contains_pyproject_toml(nested) is True


def test_has_pyproject_toml_with_empty_file(tmp_path):
    """Verify that folder_contains_pyproject_toml returns True even for empty pyproject.toml."""
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text("")

    assert folder_contains_pyproject_toml(tmp_path) is True


def test_has_pyproject_toml_with_symlink_to_directory(tmp_path):
    """Verify that folder_contains_pyproject_toml works with symlinked directories."""
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "pyproject.toml").write_text("[project]\nname = 'real'\n")

    # Create symlink to directory
    symlink_dir = tmp_path / "link"
    symlink_dir.symlink_to(real_dir)

    assert folder_contains_pyproject_toml(symlink_dir) is True


def test_has_pyproject_toml_with_symlink_file(tmp_path):
    """Verify that folder_contains_pyproject_toml detects symlinked pyproject.toml files."""
    # Create pyproject.toml in one location
    real_file = tmp_path / "real_pyproject.toml"
    real_file.write_text("[project]\nname = 'test'\n")

    # Create symlink to it
    symlink_file = tmp_path / "pyproject.toml"
    symlink_file.symlink_to(real_file)

    assert folder_contains_pyproject_toml(tmp_path) is True
