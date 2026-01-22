"""Tests for mf-clear-cache CLI command.

This module tests the mf_clear_cache command-line interface function,
including success scenarios with and without cached items, error handling,
and custom output options.
"""
import pytest
from unittest.mock import patch, mock_open

from mixinforge.command_line_tools._cli_entry_points import mf_clear_cache

# Import context managers from conftest
from .conftest import mock_sys_argv, capture_stderr, capture_stdout


@patch('mixinforge.command_line_tools._cli_entry_points.remove_python_cache_files')
def test_mf_clear_cache_success_with_items(mock_remove, project_with_pyproject):
    """Test successful execution of mf_clear_cache with items removed."""
    # Mock remove function to return some removed items
    mock_remove.return_value = (3, ["__pycache__", "file.pyc", ".pytest_cache"])

    with mock_sys_argv(['mf-clear-cache', str(project_with_pyproject)]):
        with patch('builtins.open', mock_open()) as mock_file:
            with capture_stdout() as mock_stdout:
                mf_clear_cache()

            # Verify remove function was called
            mock_remove.assert_called_once_with(project_with_pyproject)

            # Verify file was written
            mock_file.assert_called_once()
            handle = mock_file()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            assert "# Cache Cleanup Report" in written_content
            assert "**Items removed:** 3" in written_content
            assert "__pycache__" in written_content

            # Verify console output (new format with statistics)
            stdout_output = mock_stdout.getvalue()
            assert "Cache clearing: 3 items removed" in stdout_output
            assert "By type:" in stdout_output
            assert "By location:" in stdout_output


@patch('mixinforge.command_line_tools._cli_entry_points.remove_python_cache_files')
def test_mf_clear_cache_success_no_items(mock_remove, project_with_pyproject):
    """Test mf_clear_cache when no cache items found."""
    # Mock remove function to return no items
    mock_remove.return_value = (0, [])

    with mock_sys_argv(['mf-clear-cache', str(project_with_pyproject)]):
        with patch('builtins.open', mock_open()) as mock_file:
            with capture_stdout() as mock_stdout:
                mf_clear_cache()

            # Verify console output (new format)
            stdout_output = mock_stdout.getvalue()
            assert "Cache clearing: project is clean (0 items removed)" in stdout_output

            # Verify report content
            handle = mock_file()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            assert "*No cache files found*" in written_content


@patch('mixinforge.command_line_tools._cli_entry_points.remove_python_cache_files')
def test_mf_clear_cache_value_error(mock_remove, project_with_pyproject):
    """Test mf_clear_cache with ValueError from remove function."""
    # Mock remove function to raise ValueError
    mock_remove.side_effect = ValueError("Cannot clean system directories")

    with mock_sys_argv(['mf-clear-cache', str(project_with_pyproject)]):
        with capture_stderr() as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                mf_clear_cache()

            assert exc_info.value.code == 1
            stderr_output = mock_stderr.getvalue()
            assert "Error" in stderr_output or "clean" in stderr_output


@patch('mixinforge.command_line_tools._cli_entry_points.remove_python_cache_files')
def test_mf_clear_cache_file_write_error(mock_remove, project_with_pyproject):
    """Test mf_clear_cache with IOError when writing report."""
    # Mock successful removal
    mock_remove.return_value = (2, ["item1", "item2"])

    with mock_sys_argv(['mf-clear-cache', str(project_with_pyproject)]):
        with patch('builtins.open', side_effect=IOError("Disk full")):
            with capture_stderr() as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    mf_clear_cache()

                assert exc_info.value.code == 1
                stderr_output = mock_stderr.getvalue()
                assert "Error" in stderr_output or "saving" in stderr_output


@patch('mixinforge.command_line_tools._cli_entry_points.remove_python_cache_files')
def test_mf_clear_cache_custom_output_filename(mock_remove, project_with_pyproject):
    """Test mf_clear_cache with custom output filename."""
    mock_remove.return_value = (1, ["cache_dir"])

    with mock_sys_argv(['mf-clear-cache', str(project_with_pyproject), '-o', 'my_report.md']):
        with patch('builtins.open', mock_open()) as mock_file:
            with capture_stdout():
                mf_clear_cache()

            # Verify correct filename was used
            call_args = mock_file.call_args[0][0]
            assert call_args.name == "my_report.md"
