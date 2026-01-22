"""Shared fixtures for CLI entry point tests.

This module provides reusable fixtures for testing command-line interface
functions, reducing code duplication across test files.
"""
import sys
import pytest
from unittest.mock import patch
from io import StringIO
from contextlib import contextmanager


@pytest.fixture
def project_with_pyproject(tmp_path):
    """Create a temporary project directory with pyproject.toml.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Path to the project directory.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'")
    return project_dir


@pytest.fixture
def sphinx_docs_structure(tmp_path):
    """Create Sphinx documentation directory structure.

    Creates docs/source/ directory with conf.py file.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Tuple of (project_dir, docs_dir, conf_file_path).
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    docs_dir = project_dir / "docs" / "source"
    docs_dir.mkdir(parents=True)
    conf_file = docs_dir / "conf.py"
    conf_file.write_text("# Sphinx configuration")
    return project_dir, docs_dir, conf_file


@pytest.fixture
def readme_with_markers(tmp_path):
    """Create README.md with MIXINFORGE_STATS markers.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Tuple of (project_dir, readme_file).
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    readme_file = project_dir / "README.md"
    readme_content = """# Project

## Statistics
<!-- MIXINFORGE_STATS_START -->
old content
<!-- MIXINFORGE_STATS_END -->

## More content
"""
    readme_file.write_text(readme_content)
    return project_dir, readme_file


@pytest.fixture
def readme_without_markers(tmp_path):
    """Create README.md without MIXINFORGE_STATS markers.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Tuple of (project_dir, readme_file).
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    readme_file = project_dir / "README.md"
    readme_file.write_text("# Project\n\nNo markers here")
    return project_dir, readme_file


@pytest.fixture
def rst_docs_with_markers(sphinx_docs_structure):
    """Create index.rst with MIXINFORGE_STATS markers.

    Args:
        sphinx_docs_structure: Fixture providing Sphinx structure.

    Returns:
        Tuple of (project_dir, index_file).
    """
    project_dir, docs_dir, _ = sphinx_docs_structure
    index_file = docs_dir / "index.rst"
    index_content = """Project Documentation
=====================

.. MIXINFORGE_STATS_START

old table

.. MIXINFORGE_STATS_END

More content
"""
    index_file.write_text(index_content)
    return project_dir, index_file


@contextmanager
def mock_sys_argv(argv_list):
    """Context manager to mock sys.argv.

    Args:
        argv_list: List of command-line arguments.

    Yields:
        None
    """
    with patch.object(sys, 'argv', argv_list):
        yield


@contextmanager
def capture_stderr():
    """Context manager to capture stderr output.

    Yields:
        StringIO object containing stderr output.
    """
    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
        yield mock_stderr


@contextmanager
def capture_stdout():
    """Context manager to capture stdout output.

    Yields:
        StringIO object containing stdout output.
    """
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        yield mock_stdout
