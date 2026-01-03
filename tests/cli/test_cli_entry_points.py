"""Tests for CLI entry point functions.

This module tests the command-line interface entry points for the project,
including mf-stats and mf-clean-cache commands along with their helper functions.
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from io import StringIO

from mixinforge._cli_entry_points import (
    _parse_cli_arguments_with_optional_output,
    _validate_output_filename_and_warn_if_exists,
    _print_error_and_exit,
    mf_get_stats,
    mf_clean_cache
)


# Tests for _parse_cli_arguments_with_optional_output function

def test_parse_with_default_directory_and_output(tmp_path, monkeypatch):
    """Test parsing with default directory (current) and default output filename."""
    # Create a temporary directory with pyproject.toml
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    # Change to the project directory
    monkeypatch.chdir(project_dir)

    # Mock sys.argv
    with patch.object(sys, 'argv', ['mf-stats']):
        target_dir, output = _parse_cli_arguments_with_optional_output(
            "Test description",
            "default_output.md"
        )

    assert target_dir == project_dir
    assert output == "default_output.md"


def test_parse_with_explicit_directory(tmp_path):
    """Test parsing with explicit directory argument."""
    project_dir = tmp_path / "explicit_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    with patch.object(sys, 'argv', ['mf-stats', str(project_dir)]):
        target_dir, output = _parse_cli_arguments_with_optional_output(
            "Test description",
            "default.md"
        )

    assert target_dir == project_dir
    assert output == "default.md"


def test_parse_with_custom_output_flag(tmp_path):
    """Test parsing with custom --output flag."""
    project_dir = tmp_path / "custom_output_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    with patch.object(sys, 'argv', ['mf-stats', str(project_dir), '--output', 'custom.md']):
        target_dir, output = _parse_cli_arguments_with_optional_output(
            "Test description",
            "default.md"
        )

    assert output == "custom.md"


def test_parse_with_short_output_flag(tmp_path):
    """Test parsing with short -o flag."""
    project_dir = tmp_path / "short_flag_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    with patch.object(sys, 'argv', ['mf-stats', str(project_dir), '-o', 'short.md']):
        target_dir, output = _parse_cli_arguments_with_optional_output(
            "Test description",
            "default.md"
        )

    assert output == "short.md"


def test_parse_invalid_directory_path(tmp_path):
    """Test parsing with invalid directory path raises error and exits."""
    # Use a path that will cause an exception when resolved
    invalid_path = "\x00invalid"

    with patch.object(sys, 'argv', ['mf-stats', invalid_path]):
        with pytest.raises(SystemExit):
            _parse_cli_arguments_with_optional_output(
                "Test description",
                "default.md"
            )


def test_parse_missing_pyproject_toml(tmp_path):
    """Test parsing directory without pyproject.toml raises error and exits."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()

    with patch.object(sys, 'argv', ['mf-stats', str(empty_dir)]):
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                _parse_cli_arguments_with_optional_output(
                    "Test description",
                    "default.md"
                )

            assert exc_info.value.code == 1
            stderr_output = mock_stderr.getvalue()
            assert "No pyproject.toml found" in stderr_output


# Tests for _validate_output_filename_and_warn_if_exists function

def test_validate_simple_filename(tmp_path):
    """Test validation with a simple filename."""
    output_file = _validate_output_filename_and_warn_if_exists(tmp_path, "output.md")

    assert output_file == tmp_path / "output.md"


def test_validate_filename_with_existing_file(tmp_path):
    """Test validation warns when file already exists."""
    existing_file = tmp_path / "existing.md"
    existing_file.write_text("old content")

    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
        output_file = _validate_output_filename_and_warn_if_exists(tmp_path, "existing.md")

        assert output_file == existing_file
        assert "Warning" in mock_stderr.getvalue()
        assert "already exists" in mock_stderr.getvalue()


def test_validate_filename_with_forward_slash_exits(tmp_path):
    """Test validation with forward slash in filename exits."""
    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
        with pytest.raises(SystemExit) as exc_info:
            _validate_output_filename_and_warn_if_exists(tmp_path, "subdir/output.md")

        assert exc_info.value.code == 1
        stderr_output = mock_stderr.getvalue()
        assert "must be a filename, not a path" in stderr_output


def test_validate_filename_with_backslash_exits(tmp_path):
    """Test validation with backslash in filename exits."""
    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
        with pytest.raises(SystemExit) as exc_info:
            _validate_output_filename_and_warn_if_exists(tmp_path, "subdir\\output.md")

        assert exc_info.value.code == 1
        stderr_output = mock_stderr.getvalue()
        assert "must be a filename, not a path" in stderr_output


# Tests for _print_error_and_exit function

def test_print_value_error():
    """Test printing ValueError exits with code 1."""
    error = ValueError("Test value error")

    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
        with pytest.raises(SystemExit) as exc_info:
            _print_error_and_exit(error)

        assert exc_info.value.code == 1
        stderr_output = mock_stderr.getvalue()
        assert "Error: Test value error" in stderr_output


def test_print_unexpected_error():
    """Test printing unexpected error exits with code 1."""
    error = RuntimeError("Unexpected runtime error")

    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
        with pytest.raises(SystemExit) as exc_info:
            _print_error_and_exit(error)

        assert exc_info.value.code == 1
        stderr_output = mock_stderr.getvalue()
        assert "Unexpected error" in stderr_output
        assert "runtime error" in stderr_output


# Tests for mf_stats CLI command

@patch('mixinforge._cli_entry_points.analyze_project')
def test_mf_stats_success(mock_analyze, tmp_path):
    """Test successful execution of mf_stats command."""
    # Setup mock project
    project_dir = tmp_path / "stats_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    # Mock analysis result
    mock_analysis = MagicMock()
    mock_analysis.to_markdown.return_value = "# Test Metrics\n\nSome stats here"
    mock_analyze.return_value = mock_analysis

    # Mock sys.argv
    with patch.object(sys, 'argv', ['mf-stats', str(project_dir)]):
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                mf_get_stats()

            # Verify analyze_project was called
            mock_analyze.assert_called_once_with(project_dir, verbose=False)

            # Verify file was written
            mock_file.assert_called_once()
            handle = mock_file()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            assert "# Project Metrics" in written_content
            assert "# Test Metrics" in written_content

            # Verify console output
            stdout_output = mock_stdout.getvalue()
            assert "Analyzing project" in stdout_output
            assert "Analysis saved" in stdout_output


@patch('mixinforge._cli_entry_points.analyze_project')
def test_mf_stats_analyze_value_error(mock_analyze, tmp_path):
    """Test mf_stats with ValueError from analyze_project."""
    project_dir = tmp_path / "error_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    # Mock analyze_project to raise ValueError
    mock_analyze.side_effect = ValueError("Invalid project structure")

    with patch.object(sys, 'argv', ['mf-stats', str(project_dir)]):
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                mf_get_stats()

            assert exc_info.value.code == 1
            assert "Error: Invalid project structure" in mock_stderr.getvalue()


@patch('mixinforge._cli_entry_points.analyze_project')
def test_mf_stats_file_write_error(mock_analyze, tmp_path):
    """Test mf_stats with IOError when writing file."""
    project_dir = tmp_path / "write_error_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    # Mock successful analysis
    mock_analysis = MagicMock()
    mock_analysis.to_markdown.return_value = "# Test Metrics"
    mock_analyze.return_value = mock_analysis

    with patch.object(sys, 'argv', ['mf-stats', str(project_dir)]):
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    mf_get_stats()

                assert exc_info.value.code == 1
                assert "Error saving file" in mock_stderr.getvalue()


# Tests for mf_clean_cache CLI command

@patch('mixinforge._cli_entry_points.remove_python_cache_files')
def test_mf_clean_cache_success_with_items(mock_remove, tmp_path):
    """Test successful execution of mf_clean_cache with items removed."""
    project_dir = tmp_path / "clean_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    # Mock remove function to return some removed items
    mock_remove.return_value = (3, ["__pycache__", "file.pyc", ".pytest_cache"])

    with patch.object(sys, 'argv', ['mf-clean-cache', str(project_dir)]):
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                mf_clean_cache()

            # Verify remove function was called
            mock_remove.assert_called_once_with(project_dir)

            # Verify file was written
            mock_file.assert_called_once()
            handle = mock_file()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            assert "# Cache Cleanup Report" in written_content
            assert "**Items removed:** 3" in written_content
            assert "__pycache__" in written_content

            # Verify console output
            stdout_output = mock_stdout.getvalue()
            assert "Successfully removed 3 cache items" in stdout_output


@patch('mixinforge._cli_entry_points.remove_python_cache_files')
def test_mf_clean_cache_success_no_items(mock_remove, tmp_path):
    """Test mf_clean_cache when no cache items found."""
    project_dir = tmp_path / "clean_empty_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    # Mock remove function to return no items
    mock_remove.return_value = (0, [])

    with patch.object(sys, 'argv', ['mf-clean-cache', str(project_dir)]):
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                mf_clean_cache()

            # Verify console output
            stdout_output = mock_stdout.getvalue()
            assert "No cache files found" in stdout_output

            # Verify report content
            handle = mock_file()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            assert "*No cache files found*" in written_content


@patch('mixinforge._cli_entry_points.remove_python_cache_files')
def test_mf_clean_cache_value_error(mock_remove, tmp_path):
    """Test mf_clean_cache with ValueError from remove function."""
    project_dir = tmp_path / "error_clean_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    # Mock remove function to raise ValueError
    mock_remove.side_effect = ValueError("Cannot clean system directories")

    with patch.object(sys, 'argv', ['mf-clean-cache', str(project_dir)]):
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                mf_clean_cache()

            assert exc_info.value.code == 1
            assert "Error: Cannot clean system directories" in mock_stderr.getvalue()


@patch('mixinforge._cli_entry_points.remove_python_cache_files')
def test_mf_clean_cache_file_write_error(mock_remove, tmp_path):
    """Test mf_clean_cache with IOError when writing report."""
    project_dir = tmp_path / "write_error_clean_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    # Mock successful removal
    mock_remove.return_value = (2, ["item1", "item2"])

    with patch.object(sys, 'argv', ['mf-clean-cache', str(project_dir)]):
        with patch('builtins.open', side_effect=IOError("Disk full")):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    mf_clean_cache()

                assert exc_info.value.code == 1
                assert "Error saving file" in mock_stderr.getvalue()


@patch('mixinforge._cli_entry_points.remove_python_cache_files')
def test_mf_clean_cache_custom_output_filename(mock_remove, tmp_path):
    """Test mf_clean_cache with custom output filename."""
    project_dir = tmp_path / "custom_clean_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

    mock_remove.return_value = (1, ["cache_dir"])

    with patch.object(sys, 'argv', ['mf-clean-cache', str(project_dir), '-o', 'my_report.md']):
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('sys.stdout', new_callable=StringIO):
                mf_clean_cache()

            # Verify correct filename was used
            call_args = mock_file.call_args[0][0]
            assert call_args.name == "my_report.md"
