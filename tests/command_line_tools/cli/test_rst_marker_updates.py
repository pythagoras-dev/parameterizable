"""Tests for RST documentation marker update functionality.

This module tests the _update_rst_docs_if_possible function that updates
Sphinx index.rst files with statistics between MIXINFORGE_STATS markers.
"""
from pathlib import Path

from mixinforge.command_line_tools._cli_entry_points import _update_rst_docs_if_possible


def test_update_rst_with_valid_markers(rst_docs_with_markers):
    """Test updating index.rst with valid MIXINFORGE_STATS markers."""
    project_dir, index_file = rst_docs_with_markers

    new_table = ".. list-table::\n   * - LOC\n     - 100"
    result = _update_rst_docs_if_possible(project_dir, new_table)

    assert result == index_file
    updated_content = index_file.read_text()
    assert ".. list-table::" in updated_content
    assert "- LOC" in updated_content
    assert "old table" not in updated_content


def test_update_rst_no_conf_file(tmp_path):
    """Test updating RST when no conf.py exists."""
    project_dir = tmp_path / "no_docs_project"
    project_dir.mkdir()

    result = _update_rst_docs_if_possible(project_dir, "table content")
    assert result is None


def test_update_rst_no_index_file(tmp_path):
    """Test updating RST when conf.py exists but no index.rst."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    docs_dir = project_dir / "docs"
    docs_dir.mkdir()
    conf_file = docs_dir / "conf.py"
    conf_file.write_text("# Config")

    result = _update_rst_docs_if_possible(project_dir, "table content")
    assert result is None


def test_update_rst_no_markers(sphinx_docs_structure):
    """Test updating RST without markers returns None."""
    project_dir, docs_dir, _ = sphinx_docs_structure
    index_file = docs_dir / "index.rst"
    index_file.write_text("Project\n=======\n\nNo markers")

    result = _update_rst_docs_if_possible(project_dir, "table content")
    assert result is None


def test_update_rst_only_start_marker(sphinx_docs_structure):
    """Test updating RST with only start marker returns None."""
    project_dir, docs_dir, _ = sphinx_docs_structure
    index_file = docs_dir / "index.rst"
    index_file.write_text(".. MIXINFORGE_STATS_START\nContent")

    result = _update_rst_docs_if_possible(project_dir, "table content")
    assert result is None


def test_update_rst_only_end_marker(sphinx_docs_structure):
    """Test updating RST with only end marker returns None."""
    project_dir, docs_dir, _ = sphinx_docs_structure
    index_file = docs_dir / "index.rst"
    index_file.write_text(".. MIXINFORGE_STATS_END\nContent")

    result = _update_rst_docs_if_possible(project_dir, "table content")
    assert result is None


def test_update_rst_no_change_needed(sphinx_docs_structure):
    """Test updating RST when content is already up to date."""
    project_dir, docs_dir, _ = sphinx_docs_structure

    table = ".. list-table::\n   * - Stats"
    index_content = f"""Documentation
=============

.. MIXINFORGE_STATS_START

{table}

.. MIXINFORGE_STATS_END
"""
    index_file = docs_dir / "index.rst"
    index_file.write_text(index_content)

    result = _update_rst_docs_if_possible(project_dir, table)
    assert result is None


def test_update_rst_preserves_surrounding_content(sphinx_docs_structure):
    """Test that updating RST preserves content before and after markers."""
    project_dir, docs_dir, _ = sphinx_docs_structure

    index_content = """Project Title
=============

Introduction text.

.. MIXINFORGE_STATS_START

old stats

.. MIXINFORGE_STATS_END

Next Section
------------
More content.
"""
    index_file = docs_dir / "index.rst"
    index_file.write_text(index_content)

    new_table = "new stats table"
    result = _update_rst_docs_if_possible(project_dir, new_table)

    assert result == index_file
    updated_content = index_file.read_text()
    assert "Project Title" in updated_content
    assert "Introduction text." in updated_content
    assert "new stats table" in updated_content
    assert "Next Section" in updated_content
    assert "More content." in updated_content
    assert "old stats" not in updated_content


def test_update_rst_read_error(sphinx_docs_structure, monkeypatch):
    """Test that IOError during index.rst read returns None."""
    project_dir, docs_dir, _ = sphinx_docs_structure
    index_file = docs_dir / "index.rst"
    index_file.write_text(".. MIXINFORGE_STATS_START\n.. MIXINFORGE_STATS_END")

    # Mock read_text to raise IOError
    original_read_text = Path.read_text

    def mock_read_text(self, *args, **kwargs):
        if self.resolve() == index_file.resolve():
            raise IOError("Simulated read error")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", mock_read_text)

    result = _update_rst_docs_if_possible(project_dir, "table")
    assert result is None


def test_update_rst_unicode_decode_error(sphinx_docs_structure, monkeypatch):
    """Test that UnicodeDecodeError during index.rst read returns None."""
    project_dir, docs_dir, _ = sphinx_docs_structure
    index_file = docs_dir / "index.rst"
    index_file.write_text(".. MIXINFORGE_STATS_START\n.. MIXINFORGE_STATS_END")

    # Mock read_text to raise UnicodeDecodeError
    original_read_text = Path.read_text

    def mock_read_text(self, *args, **kwargs):
        if self.resolve() == index_file.resolve():
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "Simulated decode error")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", mock_read_text)

    result = _update_rst_docs_if_possible(project_dir, "table")
    assert result is None


def test_update_rst_write_error(sphinx_docs_structure, monkeypatch):
    """Test that IOError during index.rst write returns None."""
    project_dir, docs_dir, _ = sphinx_docs_structure
    index_content = """Documentation
=============

.. MIXINFORGE_STATS_START

old table

.. MIXINFORGE_STATS_END
"""
    index_file = docs_dir / "index.rst"
    index_file.write_text(index_content)

    # Mock write_text to raise IOError
    original_write_text = Path.write_text

    def mock_write_text(self, *args, **kwargs):
        if self.resolve() == index_file.resolve():
            raise IOError("Simulated write error")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", mock_write_text)

    result = _update_rst_docs_if_possible(project_dir, "new table")
    assert result is None
