from .project_analyzer import *

def mf_stats():
    """CLI entry point for generating project metrics.

    Analyzes the current directory and generates a project_metrics.md file
    with code statistics.
    """
    import sys
    from pathlib import Path

    # Get the directory to analyze (current directory by default)
    target_dir = Path.cwd()

    print(f"Analyzing project at: {target_dir}")

    # Analyze the project
    analysis = analyze_project(target_dir, verbose=False)

    # Convert to markdown
    markdown_content = analysis.to_markdown()

    # Save to file
    output_file = target_dir / 'project_metrics.md'
    try:
        with open(output_file, 'w') as f:
            f.write('# Project Metrics\n\n')
            f.write(markdown_content)
            f.write('\n')
        print(f'\n✓ Analysis saved to {output_file}')
    except IOError as e:
        print(f'\n✗ Error saving file: {e}', file=sys.stderr)
        sys.exit(1)

    # Print the results
    print('\nCurrent metrics:')
    print(markdown_content)