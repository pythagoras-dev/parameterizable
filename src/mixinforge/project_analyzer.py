"""Python project code analysis tools for development metrics.

This module provides utilities for analyzing Python codebases to extract
statistics about lines of code, classes, functions, and file counts. It
distinguishes between main source code and test code.

Note:
    This module is intended for development-time analysis only and is
    not used at runtime.
"""
import ast
from dataclasses import dataclass
from pathlib import Path


def validate_path(path: Path | str, must_exist: bool = True, must_be_dir: bool = False) -> Path:
    """Validate and sanitize a file path for secure access.

    Ensures the path is valid, resolves it to an absolute normalized form,
    and checks for path traversal attempts. This prevents directory traversal
    vulnerabilities and ensures consistent path handling.

    Args:
        path: Path to validate; accepts string or Path object.
        must_exist: Whether the path must exist on the filesystem.
        must_be_dir: Whether the path must be a directory (if it exists).

    Returns:
        Resolved absolute Path object with normalized components.

    Raises:
        ValueError: If path is None, empty, invalid, doesn't exist when required,
            or contains suspicious patterns.
        TypeError: If path is not a string or Path object.
    """
    if path is None:
        raise ValueError("Path cannot be None")

    if not isinstance(path, (str, Path)):
        raise TypeError(f"Path must be a string or Path object, got {type(path)}")

    if isinstance(path, str):
        if not path.strip():
            raise ValueError("Path cannot be empty or whitespace")
        path = Path(path)

    try:
        resolved_path = path.resolve()
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid path: {e}")

    if must_exist and not resolved_path.exists():
        raise ValueError(f"Path does not exist: {resolved_path}")

    if must_be_dir and resolved_path.exists() and not resolved_path.is_dir():
        raise ValueError(f"Path is not a directory: {resolved_path}")

    return resolved_path


def is_path_within_root(file_path: Path, root_path: Path) -> bool:
    """Check if a file path is within the root directory.

    Prevents directory traversal by verifying that the resolved file path
    is a descendant of the root path.

    Args:
        file_path: Path to check for containment.
        root_path: Root directory that should contain the file.

    Returns:
        True if file_path is within root_path, False otherwise.
    """
    try:
        file_path.resolve().relative_to(root_path.resolve())
        return True
    except ValueError:
        return False


@dataclass
class CodeStats:
    """Code statistics for source files.

    Tracks metrics for a collection of Python files, such as lines of code,
    number of classes, functions, and file count.

    Attributes:
        lines: Total lines of code.
        classes: Total number of class definitions.
        functions: Total number of function and method definitions.
        files: Total number of files analyzed.
    """
    lines: int = 0
    classes: int = 0
    functions: int = 0
    files: int = 0

    def __add__(self, other: 'CodeStats') -> 'CodeStats':
        """Combine statistics from two CodeStats instances."""
        return CodeStats(
            lines=self.lines + other.lines,
            classes=self.classes + other.classes,
            functions=self.functions + other.functions,
            files=self.files + other.files
        )


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
        lines_of_code: Line count metrics.
        classes: Class definition count metrics.
        functions: Function and method count metrics.
        files: File count metrics.
    """
    lines_of_code: MetricRow
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
            'Lines Of Code': self.lines_of_code.to_dict(),
            'Classes': self.classes.to_dict(),
            'Functions / Methods': self.functions.to_dict(),
            'Files': self.files.to_dict()
        }

    def print_summary(self) -> None:
        """Print formatted summary table to stdout."""
        print("\nSummary:")
        for metric_name, metric_dict in self.to_dict().items():
            print(f"{metric_name:20} | Main: {metric_dict['Main code']:4} | "
                  f"Tests: {metric_dict['Unit Tests']:4} | Total: {metric_dict['Total']:4}")


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
        validated_path = validate_path(file_path, must_exist=True, must_be_dir=False)

        if root_path is not None:
            validated_root = validate_path(root_path, must_exist=True, must_be_dir=True)
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

    content = None
    try:
        with open(validated_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except (FileNotFoundError, IOError, UnicodeDecodeError) as e:
        print(f"Error reading file {validated_path}: {e}")
        return CodeStats()
    except Exception as e:
        print(f"Unexpected error reading file {validated_path}: {e}")
        return CodeStats()

    if content is None:
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

        return CodeStats(lines=lines, classes=classes, functions=functions, files=1)
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

    EXCLUDE_DIRS = {'.venv', 'venv', '__pycache__', '.pytest_cache', '.tox',
                    'build', 'dist', '.git', '.eggs', 'htmlcov', 'htmlReport',
                    '.mypy_cache', '.coverage', 'node_modules', 'docs'}

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
    empty_row = MetricRow(0, 0, 0)
    return ProjectAnalysis(
        lines_of_code=empty_row,
        classes=empty_row,
        functions=empty_row,
        files=empty_row
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
        - lines_of_code: Line counts for main code, tests, and total
        - classes: Class counts for main code, tests, and total
        - functions: Function/method counts for main code, tests, and total
        - files: File counts for main code, tests, and total

        The result can be converted to dict via .to_dict() method, which is
        directly convertible to pandas DataFrame via: pd.DataFrame(result).T
    """
    try:
        validated_root = validate_path(path_to_root, must_exist=True, must_be_dir=True)
    except (ValueError, TypeError) as e:
        print(f"Invalid root path: {e}")
        return empty_analysis()

    if verbose:
        print(f"Analyzing project at: {validated_root}")

    main_code = CodeStats()
    unit_tests = CodeStats()

    try:
        for file_path in validated_root.rglob('*.py'):
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
        print(f"Error accessing directory during analysis: {e}")
        return empty_analysis()
    except Exception as e:
        print(f"Unexpected error during project analysis: {e}")
        return empty_analysis()

    total = main_code + unit_tests

    analysis = ProjectAnalysis(
        lines_of_code=MetricRow(main_code.lines, unit_tests.lines, total.lines),
        classes=MetricRow(main_code.classes, unit_tests.classes, total.classes),
        functions=MetricRow(main_code.functions, unit_tests.functions, total.functions),
        files=MetricRow(main_code.files, unit_tests.files, total.files)
    )


    return analysis



