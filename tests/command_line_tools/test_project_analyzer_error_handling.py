"""Tests for error handling in project_analyzer.py.

This module tests error handling paths including OSError, IOError,
and other exceptions during file analysis and project traversal.
"""
from pathlib import Path

from mixinforge.command_line_tools.project_analyzer import (
    analyze_file,
    analyze_project,
    CodeStats
)


def test_analyze_file_oserror_during_stat(tmp_path, monkeypatch, capsys):
    """Test analyze_file handles OSError during file.stat()."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    # Mock Path.stat to raise OSError
    original_stat = Path.stat

    def mock_stat(self, *, follow_symlinks=True):
        if self == test_file:
            raise OSError("Simulated stat error")
        return original_stat(self, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(Path, "stat", mock_stat)

    result = analyze_file(test_file)

    assert result == CodeStats()
    captured = capsys.readouterr()
    assert "Error accessing file" in captured.out


def test_analyze_file_ioerror_during_read(tmp_path, monkeypatch, capsys):
    """Test analyze_file handles IOError when opening file."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    # Mock open to raise IOError
    original_open = open

    def mock_open(*args, **kwargs):
        # Check if args[0] is a path-like object pointing to test_file
        if args:
            try:
                if Path(args[0]).resolve() == test_file.resolve():
                    raise IOError("Simulated read error")
            except (TypeError, ValueError):
                pass  # Not a valid path, proceed normally
        return original_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    result = analyze_file(test_file)

    assert result == CodeStats()
    captured = capsys.readouterr()
    assert "Error reading file" in captured.out


def test_analyze_file_unexpected_exception(tmp_path, monkeypatch, capsys):
    """Test analyze_file handles unexpected exceptions during read."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    # Mock open to raise unexpected exception
    original_open = open

    def mock_open(*args, **kwargs):
        # Check if args[0] is a path-like object pointing to test_file
        if args:
            try:
                if Path(args[0]).resolve() == test_file.resolve():
                    raise RuntimeError("Unexpected error")
            except (TypeError, ValueError):
                pass  # Not a valid path, proceed normally
        return original_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    result = analyze_file(test_file)

    assert result == CodeStats()
    captured = capsys.readouterr()
    assert "Unexpected error reading file" in captured.out


def test_analyze_project_oserror_during_iteration(tmp_path, monkeypatch, capsys):
    """Test analyze_project handles OSError during directory iteration."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Mock rglob to raise OSError
    original_rglob = Path.rglob

    def mock_rglob(self, pattern):
        if self.resolve() == project_dir.resolve():
            raise OSError("Simulated iteration error")
        return original_rglob(self, pattern)

    monkeypatch.setattr(Path, "rglob", mock_rglob)

    result = analyze_project(project_dir)

    # Should return empty analysis on OSError
    assert result.files.total == 0
    assert result.lines_of_code.total == 0
    captured = capsys.readouterr()
    assert "Error accessing directory" in captured.out


def test_analyze_project_permission_error_on_file(tmp_path, capsys):
    """Test analyze_project continues when PermissionError on individual file."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Create a valid Python file
    good_file = project_dir / "good.py"
    good_file.write_text("x = 1")

    # Create a file that will be mocked to raise PermissionError
    bad_file = project_dir / "bad.py"
    bad_file.write_text("y = 2")

    # Run with verbose to capture error message
    result = analyze_project(project_dir, verbose=True)

    # Should still analyze the good file
    assert result.files.main_code >= 1


def test_analyze_project_unexpected_exception_caught(tmp_path, monkeypatch, capsys):
    """Test analyze_project handles unexpected exceptions during iteration."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Mock rglob to raise unexpected exception
    original_rglob = Path.rglob

    def mock_rglob(self, pattern):
        if self.resolve() == project_dir.resolve():
            raise RuntimeError("Unexpected iteration error")
        return original_rglob(self, pattern)

    monkeypatch.setattr(Path, "rglob", mock_rglob)

    result = analyze_project(project_dir)

    # Should return empty analysis on unexpected error
    assert result.files.total == 0
    assert result.lines_of_code.total == 0
    captured = capsys.readouterr()
    assert "Unexpected error during project analysis" in captured.out
