"""Tests for basic_file_utils.py functionality.

Tests cover detection of pyproject.toml files in project directories,
including path validation and error handling.
"""
import pytest

from mixinforge.command_line_tools.basic_file_utils import folder_contains_pyproject_toml, remove_python_cache_files


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
    with pytest.raises(ValueError, match=r"Path.*None"):
        folder_contains_pyproject_toml(None)


def test_has_pyproject_toml_raises_on_empty_string():
    """Verify that folder_contains_pyproject_toml raises ValueError for empty string."""
    with pytest.raises(ValueError, match=r"empty"):
        folder_contains_pyproject_toml("")


def test_has_pyproject_toml_raises_on_whitespace_string():
    """Verify that folder_contains_pyproject_toml raises ValueError for whitespace string."""
    with pytest.raises(ValueError, match=r"empty"):
        folder_contains_pyproject_toml("   ")


def test_has_pyproject_toml_raises_on_invalid_type():
    """Verify that folder_contains_pyproject_toml raises TypeError for invalid type."""
    with pytest.raises(TypeError, match=r"string.*Path"):
        folder_contains_pyproject_toml(123)


def test_has_pyproject_toml_raises_on_nonexistent_folder(tmp_path):
    """Verify that folder_contains_pyproject_toml raises ValueError for nonexistent folder."""
    nonexistent = tmp_path / "does_not_exist"

    with pytest.raises(ValueError, match=r"does not exist"):
        folder_contains_pyproject_toml(nonexistent)


def test_has_pyproject_toml_raises_on_file_path(tmp_path):
    """Verify that folder_contains_pyproject_toml raises ValueError when path is a file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    with pytest.raises(ValueError, match=r"not a directory"):
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


# ============================================================================
# remove_python_cache_files tests - Basic functionality
# ============================================================================

def test_remove_python_cache_files_removes_pycache_dirs(tmp_path):
    """Verify that remove_python_cache_files removes __pycache__ directories."""
    # Create __pycache__ directories
    pycache1 = tmp_path / "__pycache__"
    pycache1.mkdir()
    (pycache1 / "test.pyc").write_text("cache")

    nested = tmp_path / "subdir"
    nested.mkdir()
    pycache2 = nested / "__pycache__"
    pycache2.mkdir()

    count, items = remove_python_cache_files(tmp_path)

    assert count == 2
    assert len(items) == 2
    assert "__pycache__" in items
    assert "subdir/__pycache__" in items
    assert not pycache1.exists()
    assert not pycache2.exists()


def test_remove_python_cache_files_removes_pyc_files(tmp_path):
    """Verify that remove_python_cache_files removes .pyc files."""
    # Create .pyc files
    (tmp_path / "module.pyc").write_text("compiled")
    nested = tmp_path / "subdir"
    nested.mkdir()
    (nested / "test.pyc").write_text("compiled")

    count, items = remove_python_cache_files(tmp_path)

    assert count == 2
    assert len(items) == 2
    assert not (tmp_path / "module.pyc").exists()
    assert not (nested / "test.pyc").exists()


def test_remove_python_cache_files_removes_pyo_files(tmp_path):
    """Verify that remove_python_cache_files removes .pyo files."""
    (tmp_path / "module.pyo").write_text("optimized")

    count, items = remove_python_cache_files(tmp_path)

    assert count == 1
    assert len(items) == 1
    assert "module.pyo" in items
    assert not (tmp_path / "module.pyo").exists()


def test_remove_python_cache_files_removes_pytest_cache(tmp_path):
    """Verify that remove_python_cache_files removes .pytest_cache directories."""
    pytest_cache = tmp_path / ".pytest_cache"
    pytest_cache.mkdir()
    (pytest_cache / "data.json").write_text("{}")

    count, items = remove_python_cache_files(tmp_path)

    assert count == 1
    assert len(items) == 1
    assert ".pytest_cache" in items
    assert not pytest_cache.exists()


def test_remove_python_cache_files_removes_mypy_cache(tmp_path):
    """Verify that remove_python_cache_files removes .mypy_cache directories."""
    mypy_cache = tmp_path / ".mypy_cache"
    mypy_cache.mkdir()

    count, items = remove_python_cache_files(tmp_path)

    assert count == 1
    assert len(items) == 1
    assert ".mypy_cache" in items
    assert not mypy_cache.exists()


def test_remove_python_cache_files_removes_ruff_cache(tmp_path):
    """Verify that remove_python_cache_files removes .ruff_cache directories."""
    ruff_cache = tmp_path / ".ruff_cache"
    ruff_cache.mkdir()

    count, items = remove_python_cache_files(tmp_path)

    assert count == 1
    assert len(items) == 1
    assert ".ruff_cache" in items
    assert not ruff_cache.exists()


def test_remove_python_cache_files_removes_hypothesis_cache(tmp_path):
    """Verify that remove_python_cache_files removes .hypothesis directories."""
    hypothesis_cache = tmp_path / ".hypothesis"
    hypothesis_cache.mkdir()

    count, items = remove_python_cache_files(tmp_path)

    assert count == 1
    assert len(items) == 1
    assert ".hypothesis" in items
    assert not hypothesis_cache.exists()


def test_remove_python_cache_files_removes_tox_cache(tmp_path):
    """Verify that remove_python_cache_files removes .tox directories."""
    tox_cache = tmp_path / ".tox"
    tox_cache.mkdir()

    count, items = remove_python_cache_files(tmp_path)

    assert count == 1
    assert len(items) == 1
    assert ".tox" in items
    assert not tox_cache.exists()


def test_remove_python_cache_files_removes_eggs_cache(tmp_path):
    """Verify that remove_python_cache_files removes .eggs directories."""
    eggs_cache = tmp_path / ".eggs"
    eggs_cache.mkdir()

    count, items = remove_python_cache_files(tmp_path)

    assert count == 1
    assert len(items) == 1
    assert ".eggs" in items
    assert not eggs_cache.exists()


def test_remove_python_cache_files_removes_coverage_files(tmp_path):
    """Verify that remove_python_cache_files removes .coverage files."""
    (tmp_path / ".coverage").write_text("data")
    (tmp_path / ".coverage.xyz").write_text("data")

    count, items = remove_python_cache_files(tmp_path)

    assert count == 2
    assert len(items) == 2
    assert not (tmp_path / ".coverage").exists()
    assert not (tmp_path / ".coverage.xyz").exists()


def test_remove_python_cache_files_preserves_regular_files(tmp_path):
    """Verify that remove_python_cache_files preserves regular Python files."""
    (tmp_path / "module.py").write_text("def func(): pass")
    (tmp_path / "test.py").write_text("def test(): pass")
    (tmp_path / "README.md").write_text("# README")

    count, items = remove_python_cache_files(tmp_path)

    assert count == 0
    assert len(items) == 0
    assert (tmp_path / "module.py").exists()
    assert (tmp_path / "test.py").exists()
    assert (tmp_path / "README.md").exists()


def test_remove_python_cache_files_handles_mixed_content(tmp_path):
    """Verify that remove_python_cache_files correctly handles mixed cache and regular files."""
    # Create regular files
    (tmp_path / "module.py").write_text("code")

    # Create cache files/dirs
    (tmp_path / "module.pyc").write_text("cache")
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    pytest_cache = tmp_path / ".pytest_cache"
    pytest_cache.mkdir()

    count, items = remove_python_cache_files(tmp_path)

    assert count == 3
    assert len(items) == 3
    assert (tmp_path / "module.py").exists()
    assert not (tmp_path / "module.pyc").exists()
    assert not pycache.exists()
    assert not pytest_cache.exists()


def test_remove_python_cache_files_works_with_nested_structure(tmp_path):
    """Verify that remove_python_cache_files works recursively in nested directories."""
    # Create nested structure
    level1 = tmp_path / "level1"
    level1.mkdir()
    level2 = level1 / "level2"
    level2.mkdir()

    # Add cache at each level
    (tmp_path / "__pycache__").mkdir()
    (level1 / "__pycache__").mkdir()
    (level2 / "test.pyc").write_text("cache")

    count, items = remove_python_cache_files(tmp_path)

    assert count == 3
    assert len(items) == 3


def test_remove_python_cache_files_returns_zero_when_no_cache(tmp_path):
    """Verify that remove_python_cache_files returns 0 when no cache files exist."""
    (tmp_path / "module.py").write_text("code")

    count, items = remove_python_cache_files(tmp_path)

    assert count == 0
    assert len(items) == 0


def test_remove_python_cache_files_accepts_string_path(tmp_path):
    """Verify that remove_python_cache_files accepts string path."""
    (tmp_path / "test.pyc").write_text("cache")

    count, items = remove_python_cache_files(str(tmp_path))

    assert count == 1
    assert len(items) == 1


def test_remove_python_cache_files_accepts_path_object(tmp_path):
    """Verify that remove_python_cache_files accepts Path object."""
    (tmp_path / "test.pyc").write_text("cache")

    count, items = remove_python_cache_files(tmp_path)

    assert count == 1
    assert len(items) == 1


# ============================================================================
# remove_python_cache_files tests - Error handling
# ============================================================================

def test_remove_python_cache_files_raises_on_none_path():
    """Verify that remove_python_cache_files raises ValueError for None path."""
    with pytest.raises(ValueError, match=r"Path.*None"):
        remove_python_cache_files(None)


def test_remove_python_cache_files_raises_on_empty_string():
    """Verify that remove_python_cache_files raises ValueError for empty string."""
    with pytest.raises(ValueError, match=r"empty"):
        remove_python_cache_files("")


def test_remove_python_cache_files_raises_on_invalid_type():
    """Verify that remove_python_cache_files raises TypeError for invalid type."""
    with pytest.raises(TypeError, match=r"string.*Path"):
        remove_python_cache_files(123)


def test_remove_python_cache_files_raises_on_nonexistent_folder(tmp_path):
    """Verify that remove_python_cache_files raises ValueError for nonexistent folder."""
    nonexistent = tmp_path / "does_not_exist"

    with pytest.raises(ValueError, match=r"does not exist"):
        remove_python_cache_files(nonexistent)


def test_remove_python_cache_files_raises_on_file_path(tmp_path):
    """Verify that remove_python_cache_files raises ValueError when path is a file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    with pytest.raises(ValueError, match=r"not a directory"):
        remove_python_cache_files(test_file)
