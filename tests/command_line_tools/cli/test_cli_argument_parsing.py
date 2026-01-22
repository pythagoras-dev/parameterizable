"""Tests for CLI argument parsing and validation functions.

This module tests the helper functions that parse command-line arguments,
validate output filenames, and handle errors.
"""
import pytest

from mixinforge.command_line_tools._cli_entry_points import (
    _parse_cli_arguments_with_optional_output,
    _validate_output_filename_and_warn_if_exists,
    _print_error_and_exit,
)

# Import context managers from conftest
from .conftest import mock_sys_argv, capture_stderr


# Tests for _parse_cli_arguments_with_optional_output function

def test_parse_with_default_directory_and_output(project_with_pyproject, monkeypatch):
    """Test parsing with default directory (current) and default output filename."""
    monkeypatch.chdir(project_with_pyproject)

    with mock_sys_argv(['mf-stats']):
        target_dir, output = _parse_cli_arguments_with_optional_output(
            "Test description",
            "default_output.md"
        )

    assert target_dir == project_with_pyproject
    assert output == "default_output.md"


def test_parse_with_explicit_directory(project_with_pyproject):
    """Test parsing with explicit directory argument."""
    with mock_sys_argv(['mf-stats', str(project_with_pyproject)]):
        target_dir, output = _parse_cli_arguments_with_optional_output(
            "Test description",
            "default.md"
        )

    assert target_dir == project_with_pyproject
    assert output == "default.md"


def test_parse_with_custom_output_flag(project_with_pyproject):
    """Test parsing with custom --output flag."""
    with mock_sys_argv(['mf-stats', str(project_with_pyproject), '--output', 'custom.md']):
        target_dir, output = _parse_cli_arguments_with_optional_output(
            "Test description",
            "default.md"
        )

    assert output == "custom.md"


def test_parse_with_short_output_flag(project_with_pyproject):
    """Test parsing with short -o flag."""
    with mock_sys_argv(['mf-stats', str(project_with_pyproject), '-o', 'short.md']):
        target_dir, output = _parse_cli_arguments_with_optional_output(
            "Test description",
            "default.md"
        )

    assert output == "short.md"


def test_parse_invalid_directory_path():
    """Test parsing with invalid directory path raises error and exits."""
    invalid_path = "\x00invalid"

    with mock_sys_argv(['mf-stats', invalid_path]):
        with pytest.raises(SystemExit):
            _parse_cli_arguments_with_optional_output(
                "Test description",
                "default.md"
            )


def test_parse_missing_pyproject_toml(tmp_path):
    """Test parsing directory without pyproject.toml raises error and exits."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()

    with mock_sys_argv(['mf-stats', str(empty_dir)]):
        with capture_stderr() as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                _parse_cli_arguments_with_optional_output(
                    "Test description",
                    "default.md"
                )

            assert exc_info.value.code == 1
            stderr_output = mock_stderr.getvalue()
            assert "pyproject.toml" in stderr_output and "found" in stderr_output


# Tests for _validate_output_filename_and_warn_if_exists function

def test_validate_simple_filename(tmp_path):
    """Test validation with a simple filename."""
    output_file = _validate_output_filename_and_warn_if_exists(tmp_path, "output.md")

    assert output_file == tmp_path / "output.md"


def test_validate_filename_with_existing_file(tmp_path):
    """Test validation warns when file already exists."""
    existing_file = tmp_path / "existing.md"
    existing_file.write_text("old content")

    with capture_stderr() as mock_stderr:
        output_file = _validate_output_filename_and_warn_if_exists(tmp_path, "existing.md")

        assert output_file == existing_file
        assert "Warning" in mock_stderr.getvalue()
        assert "already exists" in mock_stderr.getvalue()


def test_validate_filename_with_forward_slash_exits(tmp_path):
    """Test validation with forward slash in filename exits."""
    with capture_stderr() as mock_stderr:
        with pytest.raises(SystemExit) as exc_info:
            _validate_output_filename_and_warn_if_exists(tmp_path, "subdir/output.md")

        assert exc_info.value.code == 1
        stderr_output = mock_stderr.getvalue()
        assert "filename" in stderr_output and "path" in stderr_output


def test_validate_filename_with_backslash_exits(tmp_path):
    """Test validation with backslash in filename exits."""
    with capture_stderr() as mock_stderr:
        with pytest.raises(SystemExit) as exc_info:
            _validate_output_filename_and_warn_if_exists(tmp_path, "subdir\\output.md")

        assert exc_info.value.code == 1
        stderr_output = mock_stderr.getvalue()
        assert "filename" in stderr_output and "path" in stderr_output


# Tests for _print_error_and_exit function

def test_print_value_error():
    """Test printing ValueError exits with code 1."""
    error = ValueError("Test value error")

    with capture_stderr() as mock_stderr:
        with pytest.raises(SystemExit) as exc_info:
            _print_error_and_exit(error)

        assert exc_info.value.code == 1
        stderr_output = mock_stderr.getvalue()
        assert "Error" in stderr_output and "value error" in stderr_output


def test_print_unexpected_error():
    """Test printing unexpected error exits with code 1."""
    error = RuntimeError("Unexpected runtime error")

    with capture_stderr() as mock_stderr:
        with pytest.raises(SystemExit) as exc_info:
            _print_error_and_exit(error)

        assert exc_info.value.code == 1
        stderr_output = mock_stderr.getvalue()
        assert "error" in stderr_output.lower()
        assert "runtime" in stderr_output.lower() or "unexpected" in stderr_output.lower()
