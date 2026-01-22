"""Tests for mf-get-stats CLI command.

This module tests the mf_get_stats command-line interface function,
including success scenarios, error handling, and file writing.
"""
import pytest
from unittest.mock import patch, mock_open, MagicMock

from mixinforge.command_line_tools._cli_entry_points import mf_get_stats

# Import context managers from conftest
from .conftest import mock_sys_argv, capture_stderr, capture_stdout


@patch('mixinforge.command_line_tools._cli_entry_points.analyze_project')
def test_mf_stats_success(mock_analyze, project_with_pyproject):
    """Test successful execution of mf_stats command."""
    # Mock analysis result
    mock_analysis = MagicMock()
    mock_analysis.to_markdown.return_value = "# Test Metrics\n\nSome stats here"
    mock_analysis.to_rst.return_value = "RST content"
    mock_analysis.to_console_table.return_value = "Console table"
    mock_analyze.return_value = mock_analysis

    with mock_sys_argv(['mf-stats', str(project_with_pyproject)]):
        with patch('builtins.open', mock_open()) as mock_file:
            with capture_stdout() as mock_stdout:
                mf_get_stats()

            # Verify analyze_project was called
            mock_analyze.assert_called_once_with(project_with_pyproject, verbose=False)

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


@patch('mixinforge.command_line_tools._cli_entry_points.analyze_project')
def test_mf_stats_analyze_value_error(mock_analyze, project_with_pyproject):
    """Test mf_stats with ValueError from analyze_project."""
    # Mock analyze_project to raise ValueError
    mock_analyze.side_effect = ValueError("Invalid project structure")

    with mock_sys_argv(['mf-stats', str(project_with_pyproject)]):
        with capture_stderr() as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                mf_get_stats()

            assert exc_info.value.code == 1
            stderr_output = mock_stderr.getvalue()
            assert "Error" in stderr_output or "Invalid" in stderr_output


@patch('mixinforge.command_line_tools._cli_entry_points.analyze_project')
def test_mf_stats_file_write_error(mock_analyze, project_with_pyproject):
    """Test mf_stats with IOError when writing file."""
    # Mock successful analysis
    mock_analysis = MagicMock()
    mock_analysis.to_markdown.return_value = "# Test Metrics"
    mock_analysis.to_rst.return_value = "RST content"
    mock_analyze.to_console_table.return_value = "Console table"
    mock_analyze.return_value = mock_analysis

    with mock_sys_argv(['mf-stats', str(project_with_pyproject)]):
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with capture_stderr() as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    mf_get_stats()

                assert exc_info.value.code == 1
                stderr_output = mock_stderr.getvalue()
                assert "Error" in stderr_output or "saving" in stderr_output
