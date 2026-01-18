import sys
import argparse
from pathlib import Path

from ..command_line_tools.project_analyzer import analyze_project
from ..command_line_tools.basic_file_utils import (
    remove_python_cache_files,
    remove_dist_artifacts,
    folder_contains_pyproject_toml,
    format_cache_statistics
)


def _parse_cli_arguments_with_optional_output(
    description: str,
    default_output_filename: str
) -> tuple[Path, str]:
    """Parse directory and optional --output arguments from command line.

    Sets up argparse with the provided description, parses the optional
    directory argument (defaulting to current directory), and an optional
    --output/-o flag for specifying output filename.

    Validates that the target directory contains a pyproject.toml file,
    ensuring the command only operates on valid Python projects.

    Args:
        description: Description of the command for --help output.
        default_output_filename: Default filename for --output option.

    Returns:
        Tuple of (resolved Path object for target directory, output filename).

    Note:
        This function exits the program with code 1 if path validation fails
        or if pyproject.toml is not found in the directory.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to process (default: current directory)'
    )
    parser.add_argument(
        '--output', '-o',
        default=default_output_filename,
        help=f'Output filename (default: {default_output_filename})'
    )
    args = parser.parse_args()

    try:
        target_dir = Path(args.directory).resolve()
        # Validate that directory contains pyproject.toml
        if not folder_contains_pyproject_toml(target_dir):
            print(f'\n✗ Error: No pyproject.toml found in {target_dir}', file=sys.stderr)
            print('This command requires a Python project directory with pyproject.toml', file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f'\n✗ Invalid directory path: {e}', file=sys.stderr)
        sys.exit(1)

    return target_dir, args.output


def _validate_output_filename_and_warn_if_exists(target_dir: Path, output_filename: str) -> Path:
    """Validate output filename and warn if file already exists.

    Validates that the output filename is just a filename (not a path) and
    constructs the full output file path. Warns if the file already exists.

    Args:
        target_dir: Directory where the file will be saved.
        output_filename: Name of the output file.

    Returns:
        Full Path object for the output file.

    Note:
        Exits with code 1 if output_filename contains path separators.
    """
    # Validate that output_filename is just a filename, not a path
    if '/' in output_filename or '\\' in output_filename:
        print(f'\n✗ Error: Output must be a filename, not a path: {output_filename}', file=sys.stderr)
        print('Use the directory argument to specify location, not the output filename.', file=sys.stderr)
        sys.exit(1)

    output_file = target_dir / output_filename

    # Warn if output file already exists
    if output_file.exists():
        print(f'⚠ Warning: {output_file} already exists and will be overwritten', file=sys.stderr)

    return output_file


def _print_error_and_exit(error: Exception) -> None:
    """Print formatted error message to stderr and exit with code 1.

    Prints a formatted error message to stderr and exits with code 1.

    Args:
        error: The exception to handle.

    Note:
        This function always exits the program with code 1.
    """
    if isinstance(error, ValueError):
        print(f'\n✗ Error: {error}', file=sys.stderr)
    else:
        print(f'\n✗ Unexpected error: {error}', file=sys.stderr)
    sys.exit(1)


def _find_readme(target_dir: Path) -> Path | None:
    """Find README file in common locations and variations.

    Searches for README files with various naming conventions in the
    project root and common documentation directories.

    Args:
        target_dir: Root directory of the project to search.

    Returns:
        Path to README file if found, None otherwise.

    Note:
        Searches in order of preference:
        - README.md (root)
        - readme.md (root)
        - Readme.md (root)
        - README.rst (root)
        - docs/README.md
        - doc/README.md
    """
    # Common README file patterns, in order of preference
    search_patterns = [
        'README.md',
        'readme.md',
        'Readme.md',
        'README.rst',
        'docs/README.md',
        'doc/README.md'
    ]

    for pattern in search_patterns:
        readme_path = target_dir / pattern
        if readme_path.exists():
            return readme_path

    return None


def _update_readme_if_possible(target_dir: Path, markdown_table: str) -> Path | None:
    """Update README with stats table if it exists and contains markers.

    Locates a README file and checks if it contains the required
    <!-- MIXINFORGE_STATS_START --> and <!-- MIXINFORGE_STATS_END --> markers. If both
    conditions are met, updates the section between the markers with the
    new stats table.

    Args:
        target_dir: Root directory of the project.
        markdown_table: The markdown table content to insert.

    Returns:
        Path to the updated README file if successful, None otherwise.

    Note:
        This function silently returns None if README doesn't exist
        or doesn't contain the required markers. No errors are raised.
        Markers must be on their own line to be recognized (prevents
        matching markers in code examples or inline code).
    """
    import re

    readme_file = _find_readme(target_dir)

    # Check if README exists
    if readme_file is None:
        return None

    try:
        content = readme_file.read_text()
    except (IOError, UnicodeDecodeError):
        return None

    # Check if markers exist on their own lines (prevents matching in code examples)
    start_pattern = r'^<!-- MIXINFORGE_STATS_START -->\s*$'
    end_pattern = r'^<!-- MIXINFORGE_STATS_END -->\s*$'

    start_matches = list(re.finditer(start_pattern, content, re.MULTILINE))
    end_matches = list(re.finditer(end_pattern, content, re.MULTILINE))

    # Require exactly one occurrence of each marker
    if len(start_matches) != 1 or len(end_matches) != 1:
        return None

    # Update the section between markers
    try:
        start_idx = start_matches[0].end()
        end_idx = end_matches[0].start()

        # Build the new content (one newline before/after since end() includes trailing newline)
        new_stats_section = f"\n{markdown_table}\n"
        new_content = content[:start_idx] + new_stats_section + content[end_idx:]

        # Check if content actually changed
        if new_content == content:
            return None

        # Write the updated content
        readme_file.write_text(new_content)
        return readme_file

    except (ValueError, IOError):
        return None


def _find_sphinx_index_rst(target_dir: Path) -> Path | None:
    """Find Sphinx index.rst file by locating conf.py first.

    Searches for Sphinx conf.py in common documentation directory locations,
    then looks for index.rst in the same directory or parent directory.

    Args:
        target_dir: Root directory of the project to search.

    Returns:
        Path to index.rst if found, None otherwise.

    Note:
        Searches in order: docs/source/, docs/, doc/source/, doc/
    """
    # Common Sphinx documentation directory patterns
    search_patterns = [
        'docs/source',
        'docs',
        'doc/source',
        'doc'
    ]

    for pattern in search_patterns:
        conf_py_path = target_dir / pattern / 'conf.py'
        if conf_py_path.exists():
            # Found conf.py, now look for index.rst in same dir or parent
            conf_dir = conf_py_path.parent

            # Check in same directory as conf.py
            index_rst = conf_dir / 'index.rst'
            if index_rst.exists():
                return index_rst

            # Check in parent directory
            index_rst = conf_dir.parent / 'index.rst'
            if index_rst.exists():
                return index_rst

    return None


def _update_rst_docs_if_possible(target_dir: Path, rst_table: str) -> Path | None:
    """Update Sphinx index.rst with stats table if it exists and contains markers.

    Locates the Sphinx index.rst file and checks if it contains the required
    .. MIXINFORGE_STATS_START and .. MIXINFORGE_STATS_END markers. If both conditions are met,
    updates the section between the markers with the new stats table.

    Args:
        target_dir: Root directory of the project.
        rst_table: The RST list-table content to insert.

    Returns:
        Path to the updated index.rst file if successful, None otherwise.

    Note:
        This function silently returns None if index.rst doesn't exist
        or doesn't contain the required markers. No errors are raised.
        Markers must be on their own line to be recognized (prevents
        matching markers in code examples or inline code).
    """
    import re

    index_rst_path = _find_sphinx_index_rst(target_dir)

    if index_rst_path is None:
        return None

    try:
        content = index_rst_path.read_text()
    except (IOError, UnicodeDecodeError):
        return None

    # Check if markers exist on their own lines (prevents matching in code examples)
    start_pattern = r'^\.\. MIXINFORGE_STATS_START\s*$'
    end_pattern = r'^\.\. MIXINFORGE_STATS_END\s*$'

    start_matches = list(re.finditer(start_pattern, content, re.MULTILINE))
    end_matches = list(re.finditer(end_pattern, content, re.MULTILINE))

    # Require exactly one occurrence of each marker
    if len(start_matches) != 1 or len(end_matches) != 1:
        return None

    # Update the section between markers
    try:
        start_idx = start_matches[0].end()
        end_idx = end_matches[0].start()

        # Build the new content (one newline before, two after for proper RST spacing)
        new_stats_section = f"\n{rst_table}\n\n"
        new_content = content[:start_idx] + new_stats_section + content[end_idx:]

        # Check if content actually changed
        if new_content == content:
            return None

        # Write the updated content
        index_rst_path.write_text(new_content)
        return index_rst_path

    except (ValueError, IOError):
        return None


def mf_get_stats():
    """CLI entry point for generating project metrics.

    Analyzes a directory and generates a project metrics file with code statistics.
    Both saves the results to a file and prints them to the console.
    """
    target_dir, output_filename = _parse_cli_arguments_with_optional_output(
        'Generate project metrics and save to file',
        'project_metrics.md'
    )

    print(f"Analyzing project at: {target_dir}")

    try:
        analysis = analyze_project(target_dir, verbose=False)
        markdown_content = analysis.to_markdown()
        rst_content = analysis.to_rst()

        # Validate output filename and get full path
        output_file = _validate_output_filename_and_warn_if_exists(target_dir, output_filename)

        # Save to file
        try:
            with open(output_file, 'w') as f:
                f.write('# Project Metrics\n\n')
                f.write(markdown_content)
                f.write('\n')
            print(f'\n✓ Analysis saved to {output_file}')
        except IOError as e:
            print(f'\n✗ Error saving file: {e}', file=sys.stderr)
            sys.exit(1)

        # Print the results in a nice table format
        print('\n' + analysis.to_console_table())

        # Track updated files for CI/CD workflows
        updated_files = []

        # Try to update README if it exists and has markers
        readme_path = _update_readme_if_possible(target_dir, markdown_content)
        if readme_path:
            relative_path = readme_path.relative_to(target_dir)
            updated_files.append(str(relative_path))

        # Try to update Sphinx docs if they exist and have markers
        rst_path = _update_rst_docs_if_possible(target_dir, rst_content)
        if rst_path:
            relative_path = rst_path.relative_to(target_dir)
            updated_files.append(str(relative_path))

        # Output updated files summary
        if updated_files:
            print(f'\n✓ UPDATED_FILES: {" ".join(updated_files)}')

    except (ValueError, Exception) as e:
        _print_error_and_exit(e)


def mf_clear_cache():
    """CLI entry point for clearing Python cache files.

    Removes all Python cache files and directories from a directory and its subdirectories,
    including __pycache__, .pyc files, and various tool caches (pytest, mypy, ruff, etc.).
    Both saves a detailed report to a file and prints a summary to the console.
    """
    from datetime import datetime

    target_dir, output_filename = _parse_cli_arguments_with_optional_output(
        'Remove Python cache files from a directory and its subdirectories',
        'cache_cleanup_report.md'
    )

    print(f"Cleaning Python cache files from: {target_dir}")

    try:
        removed_count, removed_items = remove_python_cache_files(target_dir)

        # Generate markdown report
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        markdown_content = f"""# Cache Cleanup Report

**Directory:** {target_dir}
**Date:** {timestamp}
**Items removed:** {removed_count}

## Removed Items

"""
        if removed_count > 0:
            for item in removed_items:
                markdown_content += f"- {item}\n"
        else:
            markdown_content += "*No cache files found*\n"

        # Validate output filename and get full path
        output_file = _validate_output_filename_and_warn_if_exists(target_dir, output_filename)

        # Save to file
        try:
            with open(output_file, 'w') as f:
                f.write(markdown_content)
            print(f'\n✓ Report saved to {output_file}')
        except IOError as e:
            print(f'\n✗ Error saving file: {e}', file=sys.stderr)
            sys.exit(1)

        # Print formatted statistics to console
        print('\n' + format_cache_statistics(removed_count, removed_items))

    except (ValueError, Exception) as e:
        _print_error_and_exit(e)


def _format_size(size_bytes: int) -> str:
    """Format a size in bytes as a human-readable string."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} bytes"


def mf_clear_dist():
    """CLI entry point for clearing distribution artifacts.

    Removes the dist/ directory created by build tools like `uv build`.
    """
    parser = argparse.ArgumentParser(
        description='Remove distribution artifacts (dist/ directory) from a Python project'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to process (default: current directory)'
    )
    args = parser.parse_args()

    try:
        target_dir = Path(args.directory).resolve()
        if not folder_contains_pyproject_toml(target_dir):
            print(f'\n✗ Error: No pyproject.toml found in {target_dir}', file=sys.stderr)
            print('This command requires a Python project directory with pyproject.toml', file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f'\n✗ Invalid directory path: {e}', file=sys.stderr)
        sys.exit(1)

    print(f"Cleaning dist/ from: {target_dir}")

    try:
        file_count, total_size = remove_dist_artifacts(target_dir)

        if file_count > 0:
            size_str = _format_size(total_size)
            print(f'\n✓ Removed dist/ directory ({file_count} files, {size_str})')
        else:
            print('\n✓ No dist/ directory found (already clean)')

    except (ValueError, OSError, Exception) as e:
        _print_error_and_exit(e)