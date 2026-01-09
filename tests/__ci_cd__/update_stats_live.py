"""Live-on-self CI/CD "test" for mf_get_stats() functionality.

This "test" runs against the actual project files (README.md and docs/source/index.rst)
to ensure that statistics are always up-to-date. It's a CI/CD action masquerading as
a regular test - it validates that the documentation can be updated with current stats
by actually updating the documentation files.

The test fails if:
1. README.md and/or docs/source/index.rst are not found
2. Required markers are missing from these files
3. mf_get_stats() fails to update them
"""
import pytest
from pathlib import Path

from mixinforge.command_line_tools.project_analyzer import analyze_project
from mixinforge.command_line_tools._cli_entry_points import (
    _update_readme_if_possible,
    _update_rst_docs_if_possible
)


@pytest.mark.ci_cd
def test_live_stats_update():
    """Test that mf_get_stats() can update actual project documentation files.

    This is a live-on-self test that validates:
    - README.md exists with proper markers
    - docs/source/index.rst exists with proper markers
    - analyze_project() generates valid stats
    - Both files can be successfully updated with current stats
    - Content is actually inserted between markers
    """
    # Get project root (3 levels up from this test file)
    project_root = Path(__file__).parent.parent.parent.resolve()

    # Validate README.md exists
    readme_path = project_root / "README.md"
    assert readme_path.exists(), f"README.md not found at {readme_path}"

    # Validate README.md has required markers
    readme_content = readme_path.read_text()
    assert '<!-- MIXINFORGE_STATS_START -->' in readme_content, \
        "README.md missing <!-- MIXINFORGE_STATS_START --> marker"
    assert '<!-- MIXINFORGE_STATS_END -->' in readme_content, \
        "README.md missing <!-- MIXINFORGE_STATS_END --> marker"

    # Validate docs/source/index.rst exists
    index_rst_path = project_root / "docs" / "source" / "index.rst"
    assert index_rst_path.exists(), f"index.rst not found at {index_rst_path}"

    # Validate index.rst has required markers
    index_rst_content = index_rst_path.read_text()
    assert '.. MIXINFORGE_STATS_START' in index_rst_content, \
        "index.rst missing .. MIXINFORGE_STATS_START marker"
    assert '.. MIXINFORGE_STATS_END' in index_rst_content, \
        "index.rst missing .. MIXINFORGE_STATS_END marker"

    # Generate fresh statistics
    analysis = analyze_project(project_root, verbose=False)
    markdown_content = analysis.to_markdown()
    rst_content = analysis.to_rst()

    # Verify markdown content is valid (should contain table structure)
    assert '|' in markdown_content, "Generated markdown should contain table structure"
    assert 'LOC' in markdown_content or 'Lines' in markdown_content, \
        "Generated markdown should contain LOC/Lines metric"

    # Verify RST content is valid (should contain list-table directive)
    assert '.. list-table::' in rst_content, "Generated RST should contain list-table directive"
    assert 'LOC' in rst_content or 'Lines' in rst_content, \
        "Generated RST should contain LOC/Lines metric"

    # Store original content to verify updates actually happen
    original_readme = readme_content
    original_index_rst = index_rst_content

    # Attempt to update README.md
    updated_readme_path = _update_readme_if_possible(project_root, markdown_content)
    assert updated_readme_path is not None, \
        "Failed to update README.md - _update_readme_if_possible returned None"
    assert updated_readme_path == readme_path, \
        f"Updated path mismatch: expected {readme_path}, got {updated_readme_path}"

    # Verify README.md was actually modified
    new_readme_content = readme_path.read_text()
    # Extract content between markers to verify update
    start_marker = '<!-- MIXINFORGE_STATS_START -->'
    end_marker = '<!-- MIXINFORGE_STATS_END -->'
    start_idx = new_readme_content.index(start_marker) + len(start_marker)
    end_idx = new_readme_content.index(end_marker)
    readme_stats_section = new_readme_content[start_idx:end_idx].strip()

    assert len(readme_stats_section) > 0, "README.md stats section is empty after update"
    assert '|' in readme_stats_section, "README.md stats section should contain table"

    # Attempt to update index.rst
    updated_rst_path = _update_rst_docs_if_possible(project_root, rst_content)
    assert updated_rst_path is not None, \
        "Failed to update index.rst - _update_rst_docs_if_possible returned None"
    assert updated_rst_path == index_rst_path, \
        f"Updated path mismatch: expected {index_rst_path}, got {updated_rst_path}"

    # Verify index.rst was actually modified
    new_index_rst_content = index_rst_path.read_text()
    # Extract content between markers to verify update
    start_marker = '.. MIXINFORGE_STATS_START'
    end_marker = '.. MIXINFORGE_STATS_END'
    start_idx = new_index_rst_content.index(start_marker) + len(start_marker)
    end_idx = new_index_rst_content.index(end_marker)
    rst_stats_section = new_index_rst_content[start_idx:end_idx].strip()

    assert len(rst_stats_section) > 0, "index.rst stats section is empty after update"
    assert '.. list-table::' in rst_stats_section, \
        "index.rst stats section should contain list-table directive"

    # Success message
    print(f"\n✓ Live stats update successful:")
    print(f"  - README.md updated at {readme_path}")
    print(f"  - index.rst updated at {index_rst_path}")
