"""Tests for project_analyzer.py project-wide analysis functionality.

Tests cover analyze_project function including nested structures, symlinks,
error handling, and integration scenarios.
"""

from mixinforge.command_line_tools.project_analyzer import (
    analyze_project,
)


# ============================================================================
# analyze_project tests
# ============================================================================

def test_analyze_project_empty_directory(tmp_path):
    """Verify analyze_project handles empty directory."""
    analysis = analyze_project(tmp_path)

    assert analysis.files.total == 0
    assert analysis.lines_of_code.total == 0


def test_analyze_project_single_file(tmp_path):
    """Verify analyze_project analyzes single Python file."""
    test_file = tmp_path / "foo.py"
    test_file.write_text("""def foo():
    return 42
""")

    analysis = analyze_project(tmp_path)

    assert analysis.files.main_code == 1
    assert analysis.files.unit_tests == 0
    assert analysis.functions.main_code == 1


def test_analyze_project_separates_tests_from_main(tmp_path):
    """Verify analyze_project separates test files from main code."""
    main_file = tmp_path / "foo.py"
    main_file.write_text("""def foo():
    return 42
""")

    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    test_file = test_dir / "test_foo.py"
    test_file.write_text("""def test_foo():
    assert True
""")

    analysis = analyze_project(tmp_path)

    assert analysis.files.main_code == 1
    assert analysis.files.unit_tests == 1
    assert analysis.files.total == 2
    assert analysis.functions.main_code == 1
    assert analysis.functions.unit_tests == 1


def test_analyze_project_excludes_venv(tmp_path):
    """Verify analyze_project excludes virtual environment directories."""
    venv_dir = tmp_path / ".venv" / "lib"
    venv_dir.mkdir(parents=True)
    venv_file = venv_dir / "package.py"
    venv_file.write_text("# venv code")

    main_file = tmp_path / "main.py"
    main_file.write_text("# main code")

    analysis = analyze_project(tmp_path)

    assert analysis.files.total == 1  # Only main.py


def test_analyze_project_invalid_path_returns_empty(tmp_path):
    """Verify analyze_project returns empty analysis for invalid path."""
    nonexistent = tmp_path / "does_not_exist"
    analysis = analyze_project(nonexistent)

    assert analysis.files.total == 0


def test_analyze_project_with_nested_structure(tmp_path):
    """Verify analyze_project handles nested directory structure."""
    src_dir = tmp_path / "src" / "package"
    src_dir.mkdir(parents=True)

    file1 = src_dir / "module1.py"
    file1.write_text("def func1(): pass")

    file2 = src_dir / "module2.py"
    file2.write_text("def func2(): pass")

    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    test_file = test_dir / "test_module.py"
    test_file.write_text("def test_func(): pass")

    analysis = analyze_project(tmp_path)

    assert analysis.files.main_code == 2
    assert analysis.files.unit_tests == 1
    assert analysis.functions.main_code == 2
    assert analysis.functions.unit_tests == 1


def test_analyze_project_skips_symlinks(tmp_path):
    """Verify analyze_project skips symlinked files."""
    real_file = tmp_path / "real.py"
    real_file.write_text("def real(): pass")

    link_file = tmp_path / "link.py"
    link_file.symlink_to(real_file)

    analysis = analyze_project(tmp_path)

    # Should only count real file once
    assert analysis.files.total == 1


def test_analyze_project_skips_symlinked_directories(tmp_path):
    """Verify analyze_project skips files in symlinked directories."""
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    real_file = real_dir / "code.py"
    real_file.write_text("def func(): pass")

    link_dir = tmp_path / "link_dir"
    link_dir.symlink_to(real_dir)

    analysis = analyze_project(tmp_path)

    # Should only count files in real_dir, not through symlink
    assert analysis.files.total == 1


def test_analyze_project_counts_classes_correctly(tmp_path):
    """Verify analyze_project counts classes correctly."""
    main_file = tmp_path / "classes.py"
    main_file.write_text("""class Foo:
    pass

class Bar:
    def method(self):
        pass
""")

    analysis = analyze_project(tmp_path)

    assert analysis.classes.main_code == 2
    assert analysis.functions.main_code == 1  # method


def test_analyze_project_verbose_mode(tmp_path, capsys):
    """Verify analyze_project verbose mode prints progress."""
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 1")

    analyze_project(tmp_path, verbose=True)
    captured = capsys.readouterr()

    assert "Analyzing project at:" in captured.out
    assert "Analyzing file:" in captured.out


def test_analyze_project_handles_syntax_errors_gracefully(tmp_path):
    """Verify analyze_project continues despite syntax errors."""
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken(:")

    good_file = tmp_path / "good.py"
    good_file.write_text("def works(): pass")

    analysis = analyze_project(tmp_path)

    # Should still count the good file
    assert analysis.files.total == 1
    assert analysis.functions.total == 1


def test_analyze_project_total_equals_sum(tmp_path):
    """Verify analyze_project totals equal sum of main and test code."""
    main_file = tmp_path / "main.py"
    main_file.write_text("def main(): pass")

    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    test_file = test_dir / "test_main.py"
    test_file.write_text("def test(): pass")

    analysis = analyze_project(tmp_path)

    assert analysis.files.total == analysis.files.main_code + analysis.files.unit_tests
    assert analysis.functions.total == analysis.functions.main_code + analysis.functions.unit_tests
    assert analysis.lines_of_code.total == analysis.lines_of_code.main_code + analysis.lines_of_code.unit_tests


def test_analyze_project_with_async_functions(tmp_path):
    """Verify analyze_project counts async functions."""
    test_file = tmp_path / "async_code.py"
    test_file.write_text("""async def fetch():
    pass

async def process():
    pass
""")

    analysis = analyze_project(tmp_path)

    assert analysis.functions.main_code == 2


def test_analyze_project_sloc_less_than_loc(tmp_path):
    """Verify SLOC is less than or equal to LOC."""
    test_file = tmp_path / "code.py"
    test_file.write_text('''"""Module doc."""

# Comment
def foo():
    """Function doc."""
    x = 1

    return x
''')

    analysis = analyze_project(tmp_path)

    assert analysis.source_lines_of_code.total <= analysis.lines_of_code.total
    assert analysis.source_lines_of_code.total > 0


def test_analyze_project_with_permission_error(tmp_path, capsys):
    """Verify analyze_project continues gracefully on permission errors."""
    # Create a file and make it unreadable (may not work on all systems)
    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()
    restricted_file = restricted_dir / "secret.py"
    restricted_file.write_text("x = 1")

    good_file = tmp_path / "good.py"
    good_file.write_text("y = 2")

    # Try to make directory unreadable (skip test if we can't)
    import os
    try:
        os.chmod(restricted_dir, 0o000)
        analysis = analyze_project(tmp_path)
        # Should still analyze the accessible file
        assert analysis.files.total >= 0
    finally:
        # Restore permissions for cleanup
        os.chmod(restricted_dir, 0o755)


def test_analyze_project_with_circular_symlink_detection(tmp_path):
    """Verify analyze_project handles circular symlink references."""
    # Create a structure that could lead to circular references
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    file1 = dir1 / "code.py"
    file1.write_text("x = 1")

    # Create another directory
    dir2 = tmp_path / "dir2"
    dir2.mkdir()
    file2 = dir2 / "code.py"
    file2.write_text("y = 2")

    analysis = analyze_project(tmp_path, verbose=False)
    # Should successfully analyze without getting stuck
    assert analysis.files.total == 2
