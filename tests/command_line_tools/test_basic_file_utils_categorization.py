"""Tests for cache file categorization in basic_file_utils.py.

This module tests the categorize_cache_items function and ensures
all cache types are properly detected and categorized.
"""

from mixinforge.command_line_tools.basic_file_utils import (
    remove_python_cache_files,
    categorize_cache_items
)


def test_categorize_ruff_cache_files(tmp_path):
    """Test categorization of .ruff_cache files."""
    # Create .ruff_cache directory
    ruff_dir = tmp_path / ".ruff_cache"
    ruff_dir.mkdir()
    (ruff_dir / "cache.db").write_text("cache")

    removed_count, removed_items = remove_python_cache_files(tmp_path)

    assert removed_count > 0
    assert any('.ruff_cache' in item for item in removed_items)

    categorized = categorize_cache_items(removed_items)
    assert categorized['by_type']['.ruff_cache'] > 0


def test_categorize_mypy_cache_files(tmp_path):
    """Test categorization of .mypy_cache files."""
    mypy_dir = tmp_path / ".mypy_cache"
    mypy_dir.mkdir()
    (mypy_dir / "cache.json").write_text("{}")

    removed_count, removed_items = remove_python_cache_files(tmp_path)

    assert removed_count > 0
    assert any('.mypy_cache' in item for item in removed_items)

    categorized = categorize_cache_items(removed_items)
    assert categorized['by_type']['.mypy_cache'] > 0


def test_categorize_hypothesis_cache_files(tmp_path):
    """Test categorization of .hypothesis cache files."""
    hyp_dir = tmp_path / ".hypothesis"
    hyp_dir.mkdir()
    (hyp_dir / "data.db").write_text("data")

    removed_count, removed_items = remove_python_cache_files(tmp_path)

    assert removed_count > 0
    assert any('.hypothesis' in item for item in removed_items)

    categorized = categorize_cache_items(removed_items)
    assert categorized['by_type']['.hypothesis'] > 0


def test_categorize_tox_cache_files(tmp_path):
    """Test categorization of .tox cache files."""
    tox_dir = tmp_path / ".tox"
    tox_dir.mkdir()
    (tox_dir / "config").write_text("config")

    removed_count, removed_items = remove_python_cache_files(tmp_path)

    assert removed_count > 0
    assert any('.tox' in item for item in removed_items)

    categorized = categorize_cache_items(removed_items)
    assert categorized['by_type']['.tox'] > 0


def test_categorize_eggs_cache_files(tmp_path):
    """Test categorization of .eggs cache files."""
    eggs_dir = tmp_path / ".eggs"
    eggs_dir.mkdir()
    (eggs_dir / "info").write_text("info")

    removed_count, removed_items = remove_python_cache_files(tmp_path)

    assert removed_count > 0
    assert any('.eggs' in item for item in removed_items)

    categorized = categorize_cache_items(removed_items)
    assert categorized['by_type']['.eggs'] > 0


def test_categorize_coverage_files(tmp_path):
    """Test categorization of .coverage files."""
    (tmp_path / ".coverage").write_text("coverage data")
    (tmp_path / ".coverage.xml").write_text("<coverage/>")

    removed_count, removed_items = remove_python_cache_files(tmp_path)

    assert removed_count >= 2
    assert any('.coverage' in item for item in removed_items)

    categorized = categorize_cache_items(removed_items)
    assert categorized['by_type']['.coverage'] >= 2


def test_categorize_mixed_cache_types(tmp_path):
    """Test categorization with multiple cache types present."""
    # Create various cache types
    (tmp_path / ".ruff_cache").mkdir()
    (tmp_path / ".ruff_cache" / "cache").write_text("data")

    (tmp_path / ".mypy_cache").mkdir()
    (tmp_path / ".mypy_cache" / "cache").write_text("data")

    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".pytest_cache" / "cache").write_text("data")

    (tmp_path / ".coverage").write_text("coverage")

    removed_count, removed_items = remove_python_cache_files(tmp_path)

    assert removed_count >= 4

    categorized = categorize_cache_items(removed_items)
    assert categorized['by_type']['.ruff_cache'] > 0
    assert categorized['by_type']['.mypy_cache'] > 0
    assert categorized['by_type']['.pytest_cache'] > 0
    assert categorized['by_type']['.coverage'] > 0


def test_remove_and_categorize_integration(tmp_path):
    """End-to-end test of cache removal and categorization."""
    # Create nested structure with multiple cache types
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / ".ruff_cache").mkdir()
    (src_dir / ".ruff_cache" / "file").write_text("data")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / ".pytest_cache").mkdir()
    (tests_dir / ".pytest_cache" / "file").write_text("data")

    removed_count, removed_items = remove_python_cache_files(tmp_path)

    assert removed_count >= 2

    categorized = categorize_cache_items(removed_items)

    # Verify by_type categorization
    assert categorized['by_type']['.ruff_cache'] > 0
    assert categorized['by_type']['.pytest_cache'] > 0

    # Verify by_location categorization
    assert 'src' in categorized['by_location']
    assert 'tests' in categorized['by_location']
    assert categorized['by_location']['src'] > 0
    assert categorized['by_location']['tests'] > 0
