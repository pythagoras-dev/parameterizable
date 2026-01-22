"""Tests for project_analyzer.py file-level analysis functionality.

Tests cover SLOC counting, individual file analysis, test file detection,
file exclusion logic, and empty analysis helper.
"""
import ast
from pathlib import Path
import pytest

from mixinforge.command_line_tools.project_analyzer import (
    count_sloc,
    analyze_file,
    is_test_file,
    should_analyze_file,
    empty_analysis,
    EXCLUDE_DIRS
)


# ============================================================================
# count_sloc tests
# ============================================================================

def test_count_sloc_simple_code():
    """Verify SLOC counting for simple code without docstrings."""
    code = """x = 1
y = 2
z = x + y"""
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 3


def test_count_sloc_excludes_blank_lines():
    """Verify SLOC excludes blank lines."""
    code = """x = 1

y = 2"""
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 2


def test_count_sloc_excludes_comments():
    """Verify SLOC excludes comment-only lines."""
    code = """# This is a comment
x = 1
# Another comment
y = 2"""
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 2


def test_count_sloc_excludes_module_docstring():
    """Verify SLOC excludes module-level docstrings."""
    code = '''"""Module docstring
spanning multiple
lines."""
x = 1'''
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 1


def test_count_sloc_excludes_function_docstring():
    """Verify SLOC excludes function docstrings."""
    code = '''def foo():
    """Function docstring."""
    return 42'''
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 2  # def line and return line


def test_count_sloc_excludes_class_docstring():
    """Verify SLOC excludes class docstrings."""
    code = '''class Foo:
    """Class docstring."""
    def __init__(self):
        pass'''
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 3  # class line, def line, pass line


def test_count_sloc_multiline_docstring():
    """Verify SLOC excludes multiline docstrings completely."""
    code = '''def foo():
    """This is a
    multiline
    docstring."""
    x = 1
    return x'''
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 3  # def, x = 1, return x


def test_count_sloc_inline_comment_counted():
    """Verify lines with code and inline comments are counted."""
    code = """x = 1  # inline comment
y = 2"""
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 2


def test_count_sloc_with_async_function_docstring():
    """Verify SLOC excludes async function docstrings."""
    code = '''async def fetch():
    """Async function docstring."""
    return await something()'''
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 2  # async def line and return line


def test_count_sloc_handles_nodes_without_docstrings():
    """Verify SLOC handles AST nodes that can't have docstrings."""
    code = '''x = 1
if x:
    y = 2
else:
    y = 3'''
    tree = ast.parse(code)
    sloc = count_sloc(tree, code)
    assert sloc == 5


# ============================================================================
# analyze_file tests
# ============================================================================

def test_analyze_file_simple_python_file(tmp_path):
    """Verify analyze_file counts basic metrics correctly."""
    test_file = tmp_path / "test.py"
    test_file.write_text("""# Comment
x = 1

def foo():
    return 42

class Bar:
    pass
""")

    stats = analyze_file(test_file)

    assert stats.files == 1
    assert stats.lines == 8
    assert stats.functions == 1
    assert stats.classes == 1
    assert stats.sloc == 5  # x=1, def, return, class, pass


def test_analyze_file_with_multiple_functions(tmp_path):
    """Verify analyze_file counts multiple functions."""
    test_file = tmp_path / "test.py"
    test_file.write_text("""def foo():
    pass

def bar():
    pass

async def baz():
    pass
""")

    stats = analyze_file(test_file)
    assert stats.functions == 3


def test_analyze_file_with_multiple_classes(tmp_path):
    """Verify analyze_file counts multiple classes."""
    test_file = tmp_path / "test.py"
    test_file.write_text("""class Foo:
    pass

class Bar:
    pass
""")

    stats = analyze_file(test_file)
    assert stats.classes == 2


def test_analyze_file_with_methods_counts_as_functions(tmp_path):
    """Verify analyze_file counts class methods as functions."""
    test_file = tmp_path / "test.py"
    test_file.write_text("""class Foo:
    def method1(self):
        pass

    def method2(self):
        pass
""")

    stats = analyze_file(test_file)
    assert stats.classes == 1
    assert stats.functions == 2


def test_analyze_file_nonexistent_returns_empty_stats(tmp_path):
    """Verify analyze_file returns empty stats for nonexistent file."""
    nonexistent = tmp_path / "nonexistent.py"
    stats = analyze_file(nonexistent)

    assert stats.lines == 0
    assert stats.files == 0


def test_analyze_file_syntax_error_returns_empty_stats(tmp_path):
    """Verify analyze_file returns empty stats for file with syntax error."""
    test_file = tmp_path / "bad_syntax.py"
    test_file.write_text("def foo(:\n    pass")

    stats = analyze_file(test_file)
    assert stats.lines == 0
    assert stats.files == 0


def test_analyze_file_with_root_path_validation(tmp_path):
    """Verify analyze_file validates file is within root path."""
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 1")

    stats = analyze_file(test_file, root_path=tmp_path)
    assert stats.files == 1


def test_analyze_file_outside_root_returns_empty(tmp_path):
    """Verify analyze_file returns empty for file outside root."""
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 1")

    other_root = tmp_path.parent / "other"
    other_root.mkdir(exist_ok=True)

    stats = analyze_file(test_file, root_path=other_root)
    assert stats.files == 0


def test_analyze_file_large_file_skipped(tmp_path):
    """Verify analyze_file skips files larger than 10MB."""
    test_file = tmp_path / "huge.py"
    # Create a file larger than 10MB
    large_content = "# " + ("x" * 11_000_000) + "\n"
    test_file.write_text(large_content)

    stats = analyze_file(test_file)
    assert stats.files == 0


def test_analyze_file_with_docstrings(tmp_path):
    """Verify analyze_file handles files with docstrings."""
    test_file = tmp_path / "test.py"
    test_file.write_text('''"""Module docstring."""

def foo():
    """Function docstring."""
    return 42
''')

    stats = analyze_file(test_file)
    assert stats.files == 1
    assert stats.functions == 1


def test_analyze_file_unicode_decode_error(tmp_path, monkeypatch):
    """Verify analyze_file handles unicode decode errors gracefully."""
    test_file = tmp_path / "binary.py"
    # Write binary content that's not valid UTF-8
    test_file.write_bytes(b'\xff\xfe' + b'x' * 100)

    stats = analyze_file(test_file)
    # Should still succeed with errors='replace' in open()
    assert stats.files == 0 or stats.files == 1


def test_analyze_file_unexpected_error_during_analysis(tmp_path, monkeypatch):
    """Verify analyze_file handles unexpected errors during AST analysis."""
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 1")

    # Mock ast.walk to raise an exception
    def mock_walk(*args):
        raise RuntimeError("Unexpected error")

    monkeypatch.setattr(ast, 'walk', mock_walk)
    stats = analyze_file(test_file)

    # Should return empty stats on error
    assert stats.files == 0


# ============================================================================
# is_test_file tests
# ============================================================================

def test_is_test_file_in_tests_directory(tmp_path):
    """Verify is_test_file detects files in tests directory."""
    test_file = tmp_path / "tests" / "test_foo.py"
    test_file.parent.mkdir()
    test_file.write_text("# test")

    assert is_test_file(test_file, tmp_path) is True


def test_is_test_file_in_test_directory(tmp_path):
    """Verify is_test_file detects files in test directory (singular)."""
    test_file = tmp_path / "test" / "foo.py"
    test_file.parent.mkdir()
    test_file.write_text("# test")

    assert is_test_file(test_file, tmp_path) is True


def test_is_test_file_with_test_prefix(tmp_path):
    """Verify is_test_file detects files with test_ prefix."""
    test_file = tmp_path / "test_foo.py"
    test_file.write_text("# test")

    assert is_test_file(test_file, tmp_path) is True


def test_is_test_file_with_test_suffix(tmp_path):
    """Verify is_test_file detects files with _test.py suffix."""
    test_file = tmp_path / "foo_test.py"
    test_file.write_text("# test")

    assert is_test_file(test_file, tmp_path) is True


def test_is_test_file_regular_file_is_false(tmp_path):
    """Verify is_test_file returns False for regular files."""
    regular_file = tmp_path / "foo.py"
    regular_file.write_text("# regular")

    assert is_test_file(regular_file, tmp_path) is False


def test_is_test_file_nested_tests_directory(tmp_path):
    """Verify is_test_file detects files in nested tests directory."""
    test_file = tmp_path / "src" / "tests" / "unit" / "test_foo.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# test")

    assert is_test_file(test_file, tmp_path) is True


def test_is_test_file_outside_root_returns_false(tmp_path):
    """Verify is_test_file returns False for files outside root."""
    outside = tmp_path.parent / "outside" / "test_foo.py"
    outside.parent.mkdir(exist_ok=True)
    outside.write_text("# test")

    assert is_test_file(outside, tmp_path) is False


def test_is_test_file_invalid_path_type_returns_false():
    """Verify is_test_file returns False for invalid path types."""
    assert is_test_file("string_path", Path("/root")) is False
    assert is_test_file(Path("/test.py"), "string_root") is False


def test_is_test_file_with_nested_subdirectories(tmp_path):
    """Verify is_test_file works with deeply nested test directories."""
    deeply_nested = tmp_path / "a" / "b" / "c" / "tests" / "d" / "e"
    deeply_nested.mkdir(parents=True)
    test_file = deeply_nested / "test_deep.py"
    test_file.write_text("# test")

    assert is_test_file(test_file, tmp_path) is True


# ============================================================================
# should_analyze_file tests
# ============================================================================

def test_should_analyze_file_regular_python_file(tmp_path):
    """Verify should_analyze_file returns True for regular Python files."""
    test_file = tmp_path / "foo.py"
    test_file.write_text("# code")

    assert should_analyze_file(test_file, tmp_path) is True


def test_should_analyze_file_excludes_venv(tmp_path):
    """Verify should_analyze_file excludes .venv directories."""
    test_file = tmp_path / ".venv" / "lib" / "foo.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    assert should_analyze_file(test_file, tmp_path) is False


def test_should_analyze_file_excludes_pycache(tmp_path):
    """Verify should_analyze_file excludes __pycache__ directories."""
    test_file = tmp_path / "__pycache__" / "foo.pyc"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    assert should_analyze_file(test_file, tmp_path) is False


def test_should_analyze_file_excludes_dotfiles_directories(tmp_path):
    """Verify should_analyze_file excludes dot-prefixed directories."""
    test_file = tmp_path / ".mypy_cache" / "foo.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    assert should_analyze_file(test_file, tmp_path) is False


def test_should_analyze_file_excludes_egg_info(tmp_path):
    """Verify should_analyze_file excludes .egg-info directories."""
    test_file = tmp_path / "package.egg-info" / "foo.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    assert should_analyze_file(test_file, tmp_path) is False


def test_should_analyze_file_excludes_docs(tmp_path):
    """Verify should_analyze_file excludes docs directory."""
    test_file = tmp_path / "docs" / "source" / "conf.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    assert should_analyze_file(test_file, tmp_path) is False


def test_should_analyze_file_excludes_build(tmp_path):
    """Verify should_analyze_file excludes build directory."""
    test_file = tmp_path / "build" / "lib" / "foo.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    assert should_analyze_file(test_file, tmp_path) is False


def test_should_analyze_file_excludes_dist(tmp_path):
    """Verify should_analyze_file excludes dist directory."""
    test_file = tmp_path / "dist" / "foo.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    assert should_analyze_file(test_file, tmp_path) is False


def test_should_analyze_file_outside_root_returns_false(tmp_path):
    """Verify should_analyze_file returns False for files outside root."""
    outside = tmp_path.parent / "outside" / "foo.py"
    outside.parent.mkdir(exist_ok=True)
    outside.write_text("# code")

    assert should_analyze_file(outside, tmp_path) is False


def test_should_analyze_file_invalid_path_type_returns_false():
    """Verify should_analyze_file returns False for invalid path types."""
    assert should_analyze_file("string_path", Path("/root")) is False
    assert should_analyze_file(Path("/foo.py"), "string_root") is False


@pytest.mark.parametrize("excluded_dir", list(EXCLUDE_DIRS))
def test_should_analyze_file_excludes_all_exclude_dirs(tmp_path, excluded_dir):
    """Verify should_analyze_file excludes all directories in EXCLUDE_DIRS."""
    test_file = tmp_path / excluded_dir / "foo.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    assert should_analyze_file(test_file, tmp_path) is False


def test_should_analyze_file_with_deeply_nested_excluded_dir(tmp_path):
    """Verify should_analyze_file excludes files in nested excluded dirs."""
    nested_excluded = tmp_path / "src" / "lib" / ".git" / "hooks"
    nested_excluded.mkdir(parents=True)
    test_file = nested_excluded / "hook.py"
    test_file.write_text("# hook")

    assert should_analyze_file(test_file, tmp_path) is False


# ============================================================================
# empty_analysis tests
# ============================================================================

def test_empty_analysis_returns_zeros():
    """Verify empty_analysis returns all zeros."""
    analysis = empty_analysis()

    assert analysis.lines_of_code.total == 0
    assert analysis.source_lines_of_code.total == 0
    assert analysis.classes.total == 0
    assert analysis.functions.total == 0
    assert analysis.files.total == 0


def test_empty_analysis_all_categories_zero():
    """Verify empty_analysis has zeros for main code and tests."""
    analysis = empty_analysis()

    assert analysis.lines_of_code.main_code == 0
    assert analysis.lines_of_code.unit_tests == 0
    assert analysis.classes.main_code == 0
    assert analysis.classes.unit_tests == 0
