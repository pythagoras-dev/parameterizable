# Contributing to parameterizable

Thank you for your interest in contributing to parameterizable! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites
- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Setting Up Development Environment

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/parameterizable.git
   cd parameterizable
   ```

2. Install dependencies using uv:
   ```bash
   uv pip install -e ".[dev]"
   ```

### Running Tests

Run the test suite using pytest:
```bash
pytest
```

## How to Contribute

### Reporting Issues
- Use the GitHub issue tracker to report bugs or request features
- Provide a clear description, steps to reproduce, and expected behavior
- Include Python version and package version information

### Submitting Changes

1. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature-name
   ```
2. Make your changes and add tests if applicable
3. Ensure all tests pass
4. Commit your changes with a descriptive message (see commit conventions below)
5. Push your branch and create a pull request

### Commit Message Conventions

We follow the same title-prefix conventions used in pandas. Below are common prefixes:

```
ENH: Enhancement, new functionality
BUG: Bug fix
DOC: Additions/updates to documentation
TST: Additions/updates to tests
BLD: Updates to the build process/scripts
PERF: Performance improvement
TYP: Type annotations
CLN: Code cleanup
```

Example: `ENH: Add support for nested parameter validation`

### Code Style
- Follow PEP 8 Python style guidelines
- Keep functions and classes focused on a single responsibility
- Write clear, concise Google-style docstrings for all public functions and classes
- Write/update documentation where appropriate
- Add type hints where appropriate

### Testing
- Add tests for new functionality
- Ensure existing tests continue to pass
- Aim for good test coverage of new code
- Tests should be placed in the `tests/` directory

## Development Workflow

1. Check that your changes don't break existing functionality
2. Add appropriate tests for new features
3. Update documentation if needed
4. Ensure your code follows the project's style guidelines
5. Submit a pull request with a clear description of changes

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Contact the maintainer: Vlad (Volodymyr) Pavlov

Thank you for contributing to parameterizable!