"""Tests for edge cases in basic_file_utils.py.

Tests cover null byte path handling, format_cache_statistics edge cases,
and other boundary conditions.
"""
import pytest

from mixinforge.command_line_tools.basic_file_utils import (
    sanitize_and_validate_path,
    format_cache_statistics,
)


# ============================================================================
# sanitize_and_validate_path tests - Null byte handling
# ============================================================================

def test_sanitize_path_raises_on_null_byte_in_string():
    """Verify that sanitize_and_validate_path raises ValueError for null bytes in string."""
    with pytest.raises(ValueError, match=r"null bytes"):
        sanitize_and_validate_path("/tmp/test\x00file")


def test_sanitize_path_raises_on_null_byte_in_path_object(tmp_path):
    """Verify that sanitize_and_validate_path raises ValueError for null bytes in Path."""
    from pathlib import Path
    # Path objects can be constructed with null bytes in some cases
    path_with_null = Path(str(tmp_path) + "/test\x00file")

    with pytest.raises(ValueError, match=r"null bytes"):
        sanitize_and_validate_path(path_with_null, must_exist=False)


def test_sanitize_path_raises_on_embedded_null_byte():
    """Verify that sanitize_and_validate_path catches embedded null bytes."""
    with pytest.raises(ValueError, match=r"null bytes"):
        sanitize_and_validate_path("before\x00after")


# ============================================================================
# format_cache_statistics tests - Edge cases
# ============================================================================

def test_format_cache_statistics_with_more_than_five_locations():
    """Verify that format_cache_statistics shows top 5 locations and aggregates others."""
    # Create items from 7 different top-level directories
    removed_items = [
        "dir1/__pycache__",
        "dir1/sub/__pycache__",
        "dir2/__pycache__",
        "dir2/sub/__pycache__",
        "dir3/__pycache__",
        "dir4/__pycache__",
        "dir5/__pycache__",
        "dir6/__pycache__",
        "dir7/__pycache__",
    ]

    output = format_cache_statistics(9, removed_items)

    # Should contain the "(others)" aggregation
    assert "(others)" in output
    # Should contain the count
    assert "9 items removed" in output


def test_format_cache_statistics_with_exactly_five_locations():
    """Verify that format_cache_statistics handles exactly 5 locations without others."""
    removed_items = [
        "dir1/__pycache__",
        "dir2/__pycache__",
        "dir3/__pycache__",
        "dir4/__pycache__",
        "dir5/__pycache__",
    ]

    output = format_cache_statistics(5, removed_items)

    # Should NOT contain the "(others)" aggregation
    assert "(others)" not in output
    assert "5 items removed" in output


def test_format_cache_statistics_with_zero_items():
    """Verify that format_cache_statistics returns clean message for zero items."""
    output = format_cache_statistics(0, [])

    assert "project is clean" in output
    assert "0 items removed" in output


def test_format_cache_statistics_with_single_item():
    """Verify that format_cache_statistics handles single item correctly."""
    removed_items = ["src/__pycache__"]

    output = format_cache_statistics(1, removed_items)

    assert "1 items removed" in output
    assert "__pycache__" in output
    assert "src" in output
