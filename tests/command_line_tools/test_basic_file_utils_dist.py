"""Tests for remove_dist_artifacts functionality in basic_file_utils.py.

Tests cover removal of dist/ directories created by build tools,
including statistics calculation and edge cases.
"""
import pytest

from mixinforge.command_line_tools.basic_file_utils import remove_dist_artifacts


# ============================================================================
# remove_dist_artifacts tests - Basic functionality
# ============================================================================

def test_remove_dist_artifacts_removes_dist_directory(tmp_path):
    """Verify that remove_dist_artifacts removes the dist/ directory."""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "package-1.0.0.tar.gz").write_bytes(b"x" * 1000)
    (dist_dir / "package-1.0.0-py3-none-any.whl").write_bytes(b"y" * 2000)

    file_count, total_size = remove_dist_artifacts(tmp_path)

    assert file_count == 2
    assert total_size == 3000
    assert not dist_dir.exists()


def test_remove_dist_artifacts_returns_zero_when_no_dist(tmp_path):
    """Verify that remove_dist_artifacts returns (0, 0) when dist/ doesn't exist."""
    # tmp_path exists but has no dist/ directory
    file_count, total_size = remove_dist_artifacts(tmp_path)

    assert file_count == 0
    assert total_size == 0


def test_remove_dist_artifacts_handles_empty_dist(tmp_path):
    """Verify that remove_dist_artifacts handles empty dist/ directory."""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    file_count, total_size = remove_dist_artifacts(tmp_path)

    assert file_count == 0
    assert total_size == 0
    assert not dist_dir.exists()


def test_remove_dist_artifacts_handles_nested_files(tmp_path):
    """Verify that remove_dist_artifacts counts files in nested directories."""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    # Create nested structure
    nested = dist_dir / "subdir"
    nested.mkdir()
    (nested / "file1.txt").write_bytes(b"a" * 100)
    (nested / "file2.txt").write_bytes(b"b" * 200)
    (dist_dir / "root_file.txt").write_bytes(b"c" * 50)

    file_count, total_size = remove_dist_artifacts(tmp_path)

    assert file_count == 3
    assert total_size == 350
    assert not dist_dir.exists()


def test_remove_dist_artifacts_accepts_string_path(tmp_path):
    """Verify that remove_dist_artifacts accepts string path."""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "file.whl").write_bytes(b"x" * 500)

    file_count, total_size = remove_dist_artifacts(str(tmp_path))

    assert file_count == 1
    assert total_size == 500


def test_remove_dist_artifacts_accepts_path_object(tmp_path):
    """Verify that remove_dist_artifacts accepts Path object."""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "file.whl").write_bytes(b"x" * 500)

    file_count, total_size = remove_dist_artifacts(tmp_path)

    assert file_count == 1
    assert total_size == 500


# ============================================================================
# remove_dist_artifacts tests - Error handling
# ============================================================================

def test_remove_dist_artifacts_raises_on_none_path():
    """Verify that remove_dist_artifacts raises ValueError for None path."""
    with pytest.raises(ValueError, match=r"Path.*None"):
        remove_dist_artifacts(None)


def test_remove_dist_artifacts_raises_on_empty_string():
    """Verify that remove_dist_artifacts raises ValueError for empty string."""
    with pytest.raises(ValueError, match=r"empty"):
        remove_dist_artifacts("")


def test_remove_dist_artifacts_raises_on_invalid_type():
    """Verify that remove_dist_artifacts raises TypeError for invalid type."""
    with pytest.raises(TypeError, match=r"string.*Path"):
        remove_dist_artifacts(123)


def test_remove_dist_artifacts_raises_on_nonexistent_folder(tmp_path):
    """Verify that remove_dist_artifacts raises ValueError for nonexistent folder."""
    nonexistent = tmp_path / "does_not_exist"

    with pytest.raises(ValueError, match=r"does not exist"):
        remove_dist_artifacts(nonexistent)


def test_remove_dist_artifacts_raises_on_file_path(tmp_path):
    """Verify that remove_dist_artifacts raises ValueError when path is a file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    with pytest.raises(ValueError, match=r"not a directory"):
        remove_dist_artifacts(test_file)


# ============================================================================
# remove_dist_artifacts tests - Edge cases
# ============================================================================

def test_remove_dist_artifacts_preserves_other_directories(tmp_path):
    """Verify that remove_dist_artifacts only removes dist/, not other directories."""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "file.whl").write_bytes(b"x" * 100)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "module.py").write_text("code")

    remove_dist_artifacts(tmp_path)

    assert not dist_dir.exists()
    assert src_dir.exists()
    assert (src_dir / "module.py").exists()


def test_remove_dist_artifacts_is_idempotent(tmp_path):
    """Verify that calling remove_dist_artifacts multiple times is safe."""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "file.whl").write_bytes(b"x" * 100)

    # First call removes the directory
    file_count1, total_size1 = remove_dist_artifacts(tmp_path)
    assert file_count1 == 1
    assert total_size1 == 100

    # Second call returns zeros (idempotent)
    file_count2, total_size2 = remove_dist_artifacts(tmp_path)
    assert file_count2 == 0
    assert total_size2 == 0
