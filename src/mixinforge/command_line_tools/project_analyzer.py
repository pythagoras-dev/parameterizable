"""Python project code analysis tools for development metrics.

This module provides utilities for analyzing Python codebases to extract
statistics about lines of code, classes, functions, and file counts. It
distinguishes between main source code and test code.

Note:
    This module is intended for development-time analysis only and is
    not used at runtime.
"""
from __future__ import annotations
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..command_line_tools.basic_file_utils import sanitize_and_validate_path, is_path_within_root

EXCLUDE_DIRS: Final[set[str]] = {'.venv', 'venv', '__pycache__', '.pytest_cache',
    '.tox','build', 'dist', '.git', '.eggs', 'htmlcov', 'htmlReport',
    '.mypy_cache', '.coverage', 'node_modules', 'docs', '.ruff_cache',
    '.ipynb_checkpoints', '__pypackages__', 'site-packages'}


@dataclass
class CodeStats:
    """Code statistics for source files.

    Tracks metrics for a collection of Python files, such as lines of code,
    number of classes, functions, and file count.

    Attributes:
        lines: Total lines of code (LOC) including blank lines and comments.
        sloc: Source lines of code (SLOC) excluding blank lines, comments, and docstrings.
        classes: Total number of class definitions.
        functions: Total number of function and method definitions.
        files: Total number of files analyzed.
    """
    lines: int = 0
    sloc: int = 0
    classes: int = 0
    functions: int = 0
    files: int = 0

    def __add__(self, other: CodeStats) -> CodeStats:
        """Combine statistics from two CodeStats instances."""
        if not isinstance(other, CodeStats):
            return NotImplemented
        return CodeStats(
            lines=self.lines + other.lines,
            sloc=self.sloc + other.sloc,
            classes=self.classes + other.classes,
            functions=self.functions + other.functions,
            files=self.files + other.files)

    def __iadd__(self, other: CodeStats) -> CodeStats:
        if not isinstance(other, CodeStats):
            return NotImplemented
        self.lines += other.lines
        self.sloc += other.sloc
        self.classes += other.classes
        self.functions += other.functions
        self.files += other.files
        return self

    def __radd__(self, other: CodeStats) -> CodeStats:
        return self.__add__(other)


@dataclass
class MetricRow:
    """Analysis results row showing breakdown by code category.

    Represents a single metric (e.g., lines of code) split into main code,
    test code, and total.

    Attributes:
        main_code: Metric value for main source code.
        unit_tests: Metric value for test code.
        total: Combined metric value for all code.
    """
    main_code: int
    unit_tests: int
    total: int

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary with human-readable keys."""
        return {
            'Main code': self.main_code,
            'Unit Tests': self.unit_tests,
            'Total': self.total
        }


@dataclass
class ProjectAnalysis:
    """Complete analysis results for a Python project.

    Contains comprehensive metrics broken down by code category (main code,
    tests, and total).

    Attributes:
        lines_of_code: Line count metrics (LOC).
        source_lines_of_code: Source line count metrics (SLOC).
        classes: Class definition count metrics.
        functions: Function and method count metrics.
        files: File count metrics.
    """
    lines_of_code: MetricRow
    source_lines_of_code: MetricRow
    classes: MetricRow
    functions: MetricRow
    files: MetricRow

    def to_dict(self) -> dict[str, dict[str, int]]:
        """Convert to nested dictionary structure compatible with pandas.

        Returns:
            Nested dictionary that can be converted to DataFrame via
            pd.DataFrame(result).T
        """
        return {
            'Lines Of Code (LOC)': self.lines_of_code.to_dict(),
            'Source Lines Of Code (SLOC)': self.source_lines_of_code.to_dict(),
            'Classes': self.classes.to_dict(),
            'Functions / Methods': self.functions.to_dict(),
            'Files': self.files.to_dict()
        }

    def to_markdown(self) -> str:
        """Convert to markdown table format.

        Returns:
            Markdown-formatted table string with project metrics.
        """
        lines = []
        lines.append("| Metric | Main code | Unit Tests | Total |")
        lines.append("|--------|-----------|------------|-------|")

        for metric_name, metric_dict in self.to_dict().items():
            lines.append(f"| {metric_name} | {metric_dict['Main code']} | "
                        f"{metric_dict['Unit Tests']} | {metric_dict['Total']} |")

        return "\n".join(lines)

    def to_rst(self) -> str:
        """Convert to reStructuredText list-table format.

        Returns:
            RST-formatted list-table string with project metrics.
        """
        lines = []
        lines.append(".. list-table::")
        lines.append("   :header-rows: 1")
        lines.append("   :widths: 40 20 20 20")
        lines.append("")
        lines.append("   * - Metric")
        lines.append("     - Main code")
        lines.append("     - Unit Tests")
        lines.append("     - Total")

        for metric_name, metric_dict in self.to_dict().items():
            lines.append(f"   * - {metric_name}")
            lines.append(f"     - {metric_dict['Main code']}")
            lines.append(f"     - {metric_dict['Unit Tests']}")
            lines.append(f"     - {metric_dict['Total']}")

        return "\n".join(lines)

    def to_console_table(self) -> str:
        """Convert to formatted console table with box-drawing characters.

        Returns:
            Beautifully formatted table string for terminal display.
        """
        from tabulate import tabulate

        # Prepare data as list of lists
        table_data = []
        for metric_name, metric_dict in self.to_dict().items():
            table_data.append([
                metric_name,
                metric_dict['Main code'],
                metric_dict['Unit Tests'],
                metric_dict['Total']
            ])

        # Format table with fancy grid and thousand separators
        return tabulate(
            table_data,
            headers=['Metric', 'Main code', 'Unit Tests', 'Total'],
            tablefmt='fancy_grid',
            intfmt=','
        )


def count_sloc(tree: ast.AST, content: str) -> int:
    """Count source lines of code, excluding blank lines, comments, and docstrings.

    Args:
        tree: Parsed AST of the file.
        content: The file content as a string.

    Returns:
        Number of source lines of code.
    """
    # Collect all docstring line ranges
    docstring_lines = set()
    for node in ast.walk(tree):
        # Only check nodes that can have docstrings
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            try:
                docstring = ast.get_docstring(node, clean=False)
                if docstring is not None:
                    # Find the string node that contains the docstring
                    if (node.body and
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                        # Mark all lines occupied by this docstring
                        start_line = node.body[0].lineno
                        end_line = node.body[0].end_lineno
                        if end_line is not None:
                            for line_num in range(start_line, end_line + 1):
                                docstring_lines.add(line_num)
            except (TypeError, AttributeError):
                # Skip nodes that can't have docstrings
                pass

    # Count lines that are not blank, not comments, and not in docstrings
    sloc = 0
    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        # Skip blank lines, comment-only lines, and docstring lines
        if stripped and not stripped.startswith('#') and line_num not in docstring_lines:
            sloc += 1

    return sloc


def analyze_file(file_path: Path | str, root_path: Path | str | None = None) -> CodeStats:
    """Analyze a single Python file and extract code statistics.

    Parses the file's AST to count classes, functions, and lines. Validates
    the file path and optionally ensures it's within a root directory to
    prevent directory traversal.

    Args:
        file_path: Path to the Python file to analyze.
        root_path: Optional root directory; if provided, file_path must be
            within this directory.

    Returns:
        CodeStats with file metrics, or empty CodeStats if analysis fails.
    """
    try:
        validated_path = sanitize_and_validate_path(file_path, must_exist=True, must_be_dir=False)

        if root_path is not None:
            validated_root = sanitize_and_validate_path(root_path, must_exist=True, must_be_dir=True)
            if not is_path_within_root(validated_path, validated_root):
                raise ValueError(f"File {validated_path} is outside root directory {validated_root}")

        # Prevent memory exhaustion from extremely large files
        file_size = validated_path.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            print(f"Warning: File {validated_path} is very large ({file_size} bytes), skipping")
            return CodeStats()

    except ValueError as e:
        print(f"Path validation error for {file_path}: {e}")
        return CodeStats()
    except OSError as e:
        print(f"Error accessing file {file_path}: {e}")
        return CodeStats()

    try:
        with open(validated_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except (FileNotFoundError, IOError, UnicodeDecodeError) as e:
        print(f"Error reading file {validated_path}: {e}")
        return CodeStats()
    except Exception as e:
        print(f"Unexpected error reading file {validated_path}: {e}")
        return CodeStats()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in file {validated_path}: {e}")
        return CodeStats()
    except Exception as e:
        print(f"Unexpected error parsing file {validated_path}: {e}")
        return CodeStats()

    try:
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        lines = len(content.splitlines())
        sloc = count_sloc(tree, content)

        return CodeStats(lines=lines, sloc=sloc, classes=classes, functions=functions, files=1)
    except Exception as e:
        print(f"Error analyzing AST for file {validated_path}: {e}")
        return CodeStats()


def is_test_file(file_path: Path, root: Path) -> bool:
    """Determine if a file is a test file based on conventions.

    Identifies test files using common Python testing conventions:
    directory names (tests/, test/), file name prefixes (test_*),
    and file name suffixes (*_test.py).

    Args:
        file_path: Path to the file to check.
        root: Root directory of the project for relative path calculation.

    Returns:
        True if the file is identified as a test file, False otherwise.
    """
    if not isinstance(file_path, Path) or not isinstance(root, Path):
        return False

    try:
        rel_path = file_path.relative_to(root).parts
    except ValueError:
        return False

    is_test = (
        any(part in ('tests', 'test') for part in rel_path) or
        file_path.name.startswith('test_') or
        file_path.name.endswith('_test.py')
    )

    return is_test


def should_analyze_file(file_path: Path, root: Path) -> bool:
    """Determine if a file should be analyzed based on exclusion patterns.

    Excludes common directories like virtual environments, build artifacts,
    version control, and cache directories.

    Args:
        file_path: Path to the file to check.
        root: Root directory of the project for relative path calculation.

    Returns:
        True if the file should be analyzed, False otherwise.
    """
    if not isinstance(file_path, Path) or not isinstance(root, Path):
        return False

    try:
        parts = file_path.relative_to(root).parts
    except ValueError:
        return False

    return not any(
        part in EXCLUDE_DIRS or
        part.startswith('.') or
        part.endswith('.egg-info')
        for part in parts
    )


def empty_analysis() -> ProjectAnalysis:
    """Create an empty analysis result for error cases."""
    return ProjectAnalysis(
        lines_of_code=MetricRow(0, 0, 0),
        source_lines_of_code=MetricRow(0, 0, 0),
        classes=MetricRow(0, 0, 0),
        functions=MetricRow(0, 0, 0),
        files=MetricRow(0, 0, 0)
    )


def analyze_project(path_to_root: Path | str, verbose: bool = False) -> ProjectAnalysis:
    """Analyze a Python project directory and return comprehensive metrics.

    Recursively scans the project directory for Python files, analyzes each
    file's AST to extract statistics, and separates metrics into main code
    and test code categories.

    Args:
        path_to_root: Path to the root directory of the project.
        verbose: Whether to print progress information for each file analyzed.

    Returns:
        ProjectAnalysis containing summary statistics broken down by:
        - lines_of_code: Line counts (LOC) including blanks and comments
        - source_lines_of_code: Source line counts (SLOC) excluding blanks and comments
        - classes: Class counts for main code, tests, and total
        - functions: Function/method counts for main code, tests, and total
        - files: File counts for main code, tests, and total

        The result can be converted to dict via .to_dict() method, which is
        directly convertible to pandas DataFrame via: pd.DataFrame(result).T
    """
    try:
        validated_root = sanitize_and_validate_path(path_to_root, must_exist=True, must_be_dir=True)
    except (ValueError, TypeError) as e:
        print(f"Invalid root path: {e}")
        return empty_analysis()

    if verbose:
        print(f"Analyzing project at: {validated_root}")

    main_code = CodeStats()
    unit_tests = CodeStats()

    try:
        for file_path in validated_root.rglob('*.py'):
            try:
                # Skip symlinked files
                if file_path.is_symlink():
                    if verbose:
                        print(f"Skipping symlinked file: {file_path}")
                    continue

                # Check if any parent is a symlink to prevent following symlinked directories
                skip_file = False
                # Track seen inodes for this specific file path to detect circular references
                seen_dirs = set()
                for parent in file_path.parents:
                    if parent == validated_root:
                        break
                    if parent.is_symlink():
                        if verbose:
                            print(f"Skipping file inside symlinked dir: {file_path}")
                        skip_file = True
                        break
                    # Track directory inodes to detect circular references within this path
                    try:
                        parent_stat = parent.stat()
                        inode = (parent_stat.st_dev, parent_stat.st_ino)
                        if inode in seen_dirs:
                            if verbose:
                                print(f"Skipping file in circular path: {file_path}")
                            skip_file = True
                            break
                        seen_dirs.add(inode)
                    except OSError:
                        pass

                if skip_file:
                    continue

                if not should_analyze_file(file_path, validated_root):
                    if verbose:
                        print(f"Skipping excluded file: {file_path}")
                    continue

                if verbose:
                    print(f"Analyzing file: {file_path}")

                stats = analyze_file(file_path, root_path=validated_root)

                if is_test_file(file_path, validated_root):
                    unit_tests += stats
                else:
                    main_code += stats

            except (OSError, PermissionError) as e:
                if verbose:
                    print(f"Error accessing {file_path}: {e}")
                continue

    except (OSError, PermissionError) as e:
        print(f"Error accessing directory during analysis: {e}")
        return empty_analysis()
    except Exception as e:
        print(f"Unexpected error during project analysis: {e}")
        return empty_analysis()

    total = main_code + unit_tests

    analysis = ProjectAnalysis(
        lines_of_code=MetricRow(main_code.lines, unit_tests.lines, total.lines),
        source_lines_of_code=MetricRow(main_code.sloc, unit_tests.sloc, total.sloc),
        classes=MetricRow(main_code.classes, unit_tests.classes, total.classes),
        functions=MetricRow(main_code.functions, unit_tests.functions, total.functions),
        files=MetricRow(main_code.files, unit_tests.files, total.files)
    )


    return analysis