"""Tests for project_analyzer.py data classes.

Tests cover CodeStats, MetricRow, and ProjectAnalysis dataclasses including
operators, conversion methods, and output formatting.
"""

from mixinforge.command_line_tools.project_analyzer import (
    CodeStats,
    MetricRow,
    ProjectAnalysis,
)


# ============================================================================
# CodeStats tests
# ============================================================================

def test_codestats_default_initialization():
    """Verify CodeStats initializes with zeros."""
    stats = CodeStats()
    assert stats.lines == 0
    assert stats.sloc == 0
    assert stats.classes == 0
    assert stats.functions == 0
    assert stats.files == 0


def test_codestats_custom_initialization():
    """Verify CodeStats initializes with custom values."""
    stats = CodeStats(lines=100, sloc=80, classes=5, functions=10, files=3)
    assert stats.lines == 100
    assert stats.sloc == 80
    assert stats.classes == 5
    assert stats.functions == 10
    assert stats.files == 3


def test_codestats_add_operator():
    """Verify CodeStats addition combines values correctly."""
    stats1 = CodeStats(lines=100, sloc=80, classes=5, functions=10, files=3)
    stats2 = CodeStats(lines=50, sloc=40, classes=2, functions=5, files=1)

    result = stats1 + stats2

    assert result.lines == 150
    assert result.sloc == 120
    assert result.classes == 7
    assert result.functions == 15
    assert result.files == 4


def test_codestats_iadd_operator():
    """Verify CodeStats in-place addition updates correctly."""
    stats1 = CodeStats(lines=100, sloc=80, classes=5, functions=10, files=3)
    stats2 = CodeStats(lines=50, sloc=40, classes=2, functions=5, files=1)

    stats1 += stats2

    assert stats1.lines == 150
    assert stats1.sloc == 120
    assert stats1.classes == 7
    assert stats1.functions == 15
    assert stats1.files == 4


def test_codestats_radd_with_zero():
    """Verify CodeStats right-addition with zero returns self."""
    stats = CodeStats(lines=100, sloc=80, classes=5, functions=10, files=3)
    result = CodeStats(0,0,0,0,0) + stats

    assert result.lines == 100
    assert result.sloc == 80
    assert result.classes == 5
    assert result.functions == 10
    assert result.files == 3


def test_codestats_radd_with_codestats():
    """Verify CodeStats right-addition with another CodeStats."""
    stats1 = CodeStats(lines=100, sloc=80, classes=5, functions=10, files=3)
    stats2 = CodeStats(lines=50, sloc=40, classes=2, functions=5, files=1)

    result = stats2.__radd__(stats1)

    assert result.lines == 150
    assert result.sloc == 120
    assert result.classes == 7
    assert result.functions == 15
    assert result.files == 4


def test_codestats_add_invalid_type_returns_notimplemented():
    """Verify adding invalid type returns NotImplemented."""
    stats = CodeStats(lines=100)
    result = stats.__add__("invalid")
    assert result is NotImplemented


def test_codestats_iadd_invalid_type_returns_notimplemented():
    """Verify in-place adding invalid type returns NotImplemented."""
    stats = CodeStats(lines=100)
    result = stats.__iadd__("invalid")
    assert result is NotImplemented


def test_codestats_sum_with_multiple_instances():
    """Verify sum() works with multiple CodeStats instances."""
    stats_list = [
        CodeStats(lines=10, sloc=8, classes=1, functions=2, files=1),
        CodeStats(lines=20, sloc=16, classes=2, functions=4, files=1),
        CodeStats(lines=30, sloc=24, classes=3, functions=6, files=1),
    ]

    result = sum(stats_list, CodeStats())

    assert result.lines == 60
    assert result.sloc == 48
    assert result.classes == 6
    assert result.functions == 12
    assert result.files == 3


def test_codestats_equality_after_operations():
    """Verify CodeStats operations preserve expected values."""
    stats1 = CodeStats(lines=10, sloc=8, classes=1, functions=2, files=1)
    stats2 = CodeStats(lines=10, sloc=8, classes=1, functions=2, files=1)

    # After adding zero, should be equal
    result1 = stats1 + CodeStats()
    assert result1.lines == stats2.lines
    assert result1.sloc == stats2.sloc


# ============================================================================
# MetricRow tests
# ============================================================================

def test_metricrow_initialization():
    """Verify MetricRow initializes correctly."""
    row = MetricRow(main_code=100, unit_tests=50, total=150)
    assert row.main_code == 100
    assert row.unit_tests == 50
    assert row.total == 150


def test_metricrow_to_dict():
    """Verify MetricRow converts to dict with correct keys."""
    row = MetricRow(main_code=100, unit_tests=50, total=150)
    result = row.to_dict()

    assert result == {
        'Main code': 100,
        'Unit Tests': 50,
        'Total': 150
    }


# ============================================================================
# ProjectAnalysis tests
# ============================================================================

def test_projectanalysis_initialization():
    """Verify ProjectAnalysis initializes correctly."""
    analysis = ProjectAnalysis(
        lines_of_code=MetricRow(100, 50, 150),
        source_lines_of_code=MetricRow(80, 40, 120),
        classes=MetricRow(5, 2, 7),
        functions=MetricRow(10, 5, 15),
        files=MetricRow(3, 1, 4)
    )

    assert analysis.lines_of_code.total == 150
    assert analysis.source_lines_of_code.total == 120
    assert analysis.classes.total == 7
    assert analysis.functions.total == 15
    assert analysis.files.total == 4


def test_projectanalysis_to_dict():
    """Verify ProjectAnalysis converts to dict correctly."""
    analysis = ProjectAnalysis(
        lines_of_code=MetricRow(100, 50, 150),
        source_lines_of_code=MetricRow(80, 40, 120),
        classes=MetricRow(5, 2, 7),
        functions=MetricRow(10, 5, 15),
        files=MetricRow(3, 1, 4)
    )

    result = analysis.to_dict()

    assert 'Lines Of Code (LOC)' in result
    assert 'Source Lines Of Code (SLOC)' in result
    assert 'Classes' in result
    assert 'Functions / Methods' in result
    assert 'Files' in result

    assert result['Lines Of Code (LOC)']['Total'] == 150
    assert result['Source Lines Of Code (SLOC)']['Main code'] == 80
    assert result['Classes']['Unit Tests'] == 2


def test_projectanalysis_to_markdown():
    """Verify ProjectAnalysis converts to markdown table."""
    analysis = ProjectAnalysis(
        lines_of_code=MetricRow(100, 50, 150),
        source_lines_of_code=MetricRow(80, 40, 120),
        classes=MetricRow(5, 2, 7),
        functions=MetricRow(10, 5, 15),
        files=MetricRow(3, 1, 4)
    )

    markdown = analysis.to_markdown()

    assert "| Metric | Main code | Unit Tests | Total |" in markdown
    assert "|--------|-----------|------------|-------|" in markdown
    assert "| Lines Of Code (LOC) | 100 | 50 | 150 |" in markdown
    assert "| Source Lines Of Code (SLOC) | 80 | 40 | 120 |" in markdown
    assert "| Classes | 5 | 2 | 7 |" in markdown
    assert "| Functions / Methods | 10 | 5 | 15 |" in markdown
    assert "| Files | 3 | 1 | 4 |" in markdown


def test_projectanalysis_markdown_format():
    """Verify ProjectAnalysis markdown output is properly formatted."""
    analysis = ProjectAnalysis(
        lines_of_code=MetricRow(1000, 500, 1500),
        source_lines_of_code=MetricRow(800, 400, 1200),
        classes=MetricRow(50, 20, 70),
        functions=MetricRow(100, 50, 150),
        files=MetricRow(30, 10, 40)
    )

    markdown = analysis.to_markdown()
    lines = markdown.split('\n')

    # Verify table structure
    assert len(lines) >= 7  # Header + separator + 5 data rows
    assert all('|' in line for line in lines)
    # Verify alignment row
    assert '|--------|' in lines[1]


def test_projectanalysis_to_console_table():
    """Verify ProjectAnalysis console table output is properly formatted with tabulate."""
    analysis = ProjectAnalysis(
        lines_of_code=MetricRow(1000, 500, 1500),
        source_lines_of_code=MetricRow(800, 400, 1200),
        classes=MetricRow(50, 20, 70),
        functions=MetricRow(100, 50, 150),
        files=MetricRow(30, 10, 40)
    )

    console_output = analysis.to_console_table()

    # Verify it returns a non-empty string
    assert isinstance(console_output, str)
    assert len(console_output) > 0

    # Verify headers are present
    assert "Metric" in console_output
    assert "Main code" in console_output
    assert "Unit Tests" in console_output
    assert "Total" in console_output

    # Verify metric names are present
    assert "Lines Of Code (LOC)" in console_output
    assert "Source Lines Of Code (SLOC)" in console_output
    assert "Classes" in console_output
    assert "Functions / Methods" in console_output
    assert "Files" in console_output

    # Verify values with thousand separators are present
    assert "1,000" in console_output
    assert "1,500" in console_output
    assert "1,200" in console_output

    # Verify box-drawing characters are present (fancy_grid format)
    assert "─" in console_output  # horizontal line
    assert "│" in console_output  # vertical line
    # Check for corner/junction characters (any of these should be present)
    box_chars = ["┌", "┐", "└", "┘", "├", "┤", "┬", "┴", "┼"]
    assert any(char in console_output for char in box_chars)
