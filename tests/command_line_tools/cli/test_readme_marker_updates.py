"""Tests for README marker update functionality.

This module tests the _update_readme_if_possible function that updates
README files with statistics between MIXINFORGE_STATS markers.
"""
from pathlib import Path

from mixinforge.command_line_tools._cli_entry_points import _update_readme_if_possible


def test_update_readme_with_valid_markers(readme_with_markers):
    """Test updating README with valid MIXINFORGE_STATS markers."""
    project_dir, readme_file = readme_with_markers

    new_table = "| Header | Value |\n|--------|-------|\n| LOC    | 100   |"
    result = _update_readme_if_possible(project_dir, new_table)

    assert result == readme_file
    updated_content = readme_file.read_text()
    assert "| Header | Value |" in updated_content
    assert "| LOC    | 100   |" in updated_content
    assert "old content" not in updated_content


def test_update_readme_no_file(tmp_path):
    """Test updating README when no README file exists."""
    project_dir = tmp_path / "no_readme_project"
    project_dir.mkdir()

    result = _update_readme_if_possible(project_dir, "table content")
    assert result is None


def test_update_readme_no_markers(readme_without_markers):
    """Test updating README without markers returns None."""
    project_dir, readme_file = readme_without_markers

    result = _update_readme_if_possible(project_dir, "table content")
    assert result is None


def test_update_readme_only_start_marker(tmp_path):
    """Test updating README with only start marker returns None."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    readme_file = project_dir / "README.md"
    readme_file.write_text("# Project\n<!-- MIXINFORGE_STATS_START -->\nContent")

    result = _update_readme_if_possible(project_dir, "table content")
    assert result is None


def test_update_readme_only_end_marker(tmp_path):
    """Test updating README with only end marker returns None."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    readme_file = project_dir / "README.md"
    readme_file.write_text("# Project\n<!-- MIXINFORGE_STATS_END -->\nContent")

    result = _update_readme_if_possible(project_dir, "table content")
    assert result is None


def test_update_readme_no_change_needed(tmp_path):
    """Test updating README when content is already up to date."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    table = "| Header | Value |"
    readme_content = f"""# Project
<!-- MIXINFORGE_STATS_START -->
{table}
<!-- MIXINFORGE_STATS_END -->
"""
    readme_file = project_dir / "README.md"
    readme_file.write_text(readme_content)

    result = _update_readme_if_possible(project_dir, table)
    assert result is None


def test_update_readme_preserves_surrounding_content(tmp_path):
    """Test that updating README preserves content before and after markers."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    readme_content = """# Project Title

Some intro text.

<!-- MIXINFORGE_STATS_START -->
old stats
<!-- MIXINFORGE_STATS_END -->

## Next Section
More content here.
"""
    readme_file = project_dir / "README.md"
    readme_file.write_text(readme_content)

    new_table = "new stats table"
    result = _update_readme_if_possible(project_dir, new_table)

    assert result == readme_file
    updated_content = readme_file.read_text()
    assert "# Project Title" in updated_content
    assert "Some intro text." in updated_content
    assert "new stats table" in updated_content
    assert "## Next Section" in updated_content
    assert "More content here." in updated_content
    assert "old stats" not in updated_content


def test_update_readme_read_error(tmp_path, monkeypatch):
    """Test that IOError during README read returns None."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    readme_file = project_dir / "README.md"
    readme_file.write_text("# Project\n<!-- MIXINFORGE_STATS_START -->\n<!-- MIXINFORGE_STATS_END -->")

    # Mock read_text to raise IOError
    original_read_text = Path.read_text

    def mock_read_text(self, *args, **kwargs):
        if self.resolve() == readme_file.resolve():
            raise IOError("Simulated read error")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", mock_read_text)

    result = _update_readme_if_possible(project_dir, "table")
    assert result is None


def test_update_readme_unicode_decode_error(tmp_path, monkeypatch):
    """Test that UnicodeDecodeError during README read returns None."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    readme_file = project_dir / "README.md"
    readme_file.write_text("# Project\n<!-- MIXINFORGE_STATS_START -->\n<!-- MIXINFORGE_STATS_END -->")

    # Mock read_text to raise UnicodeDecodeError
    original_read_text = Path.read_text

    def mock_read_text(self, *args, **kwargs):
        if self.resolve() == readme_file.resolve():
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "Simulated decode error")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", mock_read_text)

    result = _update_readme_if_possible(project_dir, "table")
    assert result is None


def test_update_readme_write_error(tmp_path, monkeypatch):
    """Test that IOError during README write returns None."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    readme_content = """# Project
<!-- MIXINFORGE_STATS_START -->
old content
<!-- MIXINFORGE_STATS_END -->
"""
    readme_file = project_dir / "README.md"
    readme_file.write_text(readme_content)

    # Mock write_text to raise IOError
    original_write_text = Path.write_text

    def mock_write_text(self, *args, **kwargs):
        if self.resolve() == readme_file.resolve():
            raise IOError("Simulated write error")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", mock_write_text)

    result = _update_readme_if_possible(project_dir, "new table")
    assert result is None
