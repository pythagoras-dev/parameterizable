"""Tests for verbose mode output in project_analyzer.py.

This module tests verbose output paths including messages for
symlinked files, circular paths, excluded files, and errors.
"""
from pathlib import Path
import pytest

from mixinforge.command_line_tools.project_analyzer import analyze_project


def test_verbose_output_with_symlinked_file(tmp_path, capsys):
    """Test verbose message is printed when skipping symlinked files."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Create a regular Python file
    real_file = project_dir / "real.py"
    real_file.write_text("x = 1")

    # Create a symlink to the Python file
    symlink_file = project_dir / "link.py"
    try:
        symlink_file.symlink_to(real_file)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on this platform")

    # Run with verbose mode
    analyze_project(project_dir, verbose=True)

    captured = capsys.readouterr()
    assert "Skipping symlinked file" in captured.out


def test_verbose_output_for_excluded_file(tmp_path, capsys):
    """Test verbose message when skipping excluded files."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Create a file in excluded directory
    venv_dir = project_dir / "venv"
    venv_dir.mkdir()
    excluded_file = venv_dir / "excluded.py"
    excluded_file.write_text("x = 1")

    # Run with verbose mode
    analyze_project(project_dir, verbose=True)

    captured = capsys.readouterr()
    assert "Skipping excluded file" in captured.out


def test_verbose_output_during_analysis(tmp_path, capsys):
    """Test verbose message is printed when analyzing files."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Create a Python file
    py_file = project_dir / "code.py"
    py_file.write_text("def foo(): pass")

    # Run with verbose mode
    analyze_project(project_dir, verbose=True)

    captured = capsys.readouterr()
    assert "Analyzing file" in captured.out


def test_verbose_output_on_permission_error(tmp_path, monkeypatch, capsys):
    """Test verbose message on PermissionError during file iteration."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Create a Python file
    py_file = project_dir / "code.py"
    py_file.write_text("def foo(): pass")

    # Mock is_symlink to raise PermissionError to trigger error path
    original_is_symlink = Path.is_symlink

    def mock_is_symlink(self):
        if self.name == "code.py":
            raise PermissionError("Simulated permission error")
        return original_is_symlink(self)

    monkeypatch.setattr(Path, "is_symlink", mock_is_symlink)

    # Run with verbose mode
    analyze_project(project_dir, verbose=True)

    captured = capsys.readouterr()
    assert "Error accessing" in captured.out


def test_verbose_output_shows_analysis_message(tmp_path, capsys):
    """Test that verbose mode shows analysis messages."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Create a Python file
    (project_dir / "code.py").write_text("x = 1")

    # Run with verbose mode
    analyze_project(project_dir, verbose=True)

    captured = capsys.readouterr()
    # Should show that we're analyzing the project
    assert "Analyzing project at:" in captured.out or "Analyzing file" in captured.out


def test_no_verbose_output_by_default(tmp_path, capsys):
    """Test that verbose messages are not printed by default."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Create a file in excluded directory
    venv_dir = project_dir / "venv"
    venv_dir.mkdir()
    excluded_file = venv_dir / "excluded.py"
    excluded_file.write_text("x = 1")

    # Run without verbose mode
    analyze_project(project_dir, verbose=False)

    captured = capsys.readouterr()
    assert "Skipping excluded file" not in captured.out
    assert "Analyzing file" not in captured.out
