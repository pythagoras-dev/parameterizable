# Read the Docs Configuration Guide

> **Purpose**: This guide provides complete configuration and best practices for building and maintaining mixinforge documentation using Sphinx and Read the Docs. Use this when setting up, updating, or troubleshooting documentation.
>
> **Audience**: Maintainers and contributors working on mixinforge documentation.

---

## Quick Reference

| Task | Command / Location |
|------|-------------------|
| Build docs locally | `cd docs && make html` |
| Test docs | `sphinx-build -b html -W --keep-going docs/source docs/build` |
| Check links | `sphinx-build -b linkcheck docs/source docs/build` |
| Config file | `docs/source/conf.py` |
| Requirements | `docs/requirements.txt` |
| Theme | `pydata_sphinx_theme` |

---

## Table of Contents

1. [Documentation Structure](#documentation-structure)
2. [Sphinx Configuration](#sphinx-configuration-confpy)
3. [Read the Docs Config](#readthedocsyaml)
4. [Dependencies](#docsrequirementstxt)
5. [Testing Documentation](#testing-documentation)
6. [Content Guidelines](#content-guidelines)
7. [Maintenance Checklist](#maintenance-checklist)
8. [Component Documentation Templates](#component-documentation-templates)
9. [Troubleshooting](#troubleshooting)
10. [Version Management](#version-management)

---

> **Related Documentation**:
> - Docstring formatting: [docstrings_comments.md](https://github.com/pythagoras-dev/mixinforge/blob/master/docstrings_comments.md)
> - Type hints: [type_hints.md](https://github.com/pythagoras-dev/mixinforge/blob/master/type_hints.md)
> - Contribution workflow: [contributing.md](https://github.com/pythagoras-dev/mixinforge/blob/master/CONTRIBUTING.md)
> - Project structure: [README.md](https://github.com/pythagoras-dev/mixinforge/blob/master/README.md)

---

## Documentation Structure

```
docs/
├── source/
│   ├── conf.py                    # Sphinx configuration
│   ├── index.rst                  # Main documentation page
│   ├── _static/                   # Static assets (CSS, images, etc.)
│   ├── _templates/                # Custom templates (optional)
│   ├── installation.rst           # Installation instructions (optional)
│   ├── quickstart.rst             # Quick start guide (optional)
│   ├── contributing.md            # Symlinked from root (optional)
│   ├── type_hints.md              # Symlinked from root (optional)
│   ├── docstrings_comments.md     # Symlinked from root (optional)
│   ├── user_guide/                # User-focused documentation (optional)
│   │   ├── index.rst
│   │   ├── mixinforge.rst
│   │   ├── cacheable_properties.rst
│   │   ├── thread_safety.rst
│   │   └── advanced_usage.rst
│   └── api/                       # Auto-generated API reference
│       ├── index.rst
│       └── modules.rst
├── requirements.txt               # Documentation dependencies
├── Makefile                       # Build commands for Unix/Mac
└── make.bat                       # Build commands for Windows
```

**Note**: The `_static/` directory must exist (even if empty) to avoid Sphinx warnings.

## Sphinx Configuration (conf.py)

### Essential Extensions
```python
extensions = [
    'sphinx.ext.autodoc',        # Auto-generate from docstrings
    'sphinx.ext.napoleon',       # Google-style docstrings
    'sphinx.ext.viewcode',       # Source code links
    'sphinx.ext.intersphinx',    # Cross-project links
    'sphinx.ext.autosummary',    # Summary tables
    'sphinx_autodoc_typehints',  # Type hint rendering
    'sphinx_copybutton',         # Copy buttons for code
    'myst_parser',               # Markdown support
]
```

### Key Settings
```python
# Version from package
from mixinforge import __version__
version = release = __version__

# Theme
html_theme = 'pydata_sphinx_theme'
html_theme_options = {
    'show_nav_level': 2,
    'navigation_depth': 4,
    'show_toc_level': 2,
    'navbar_align': 'left',
}

# Autodoc
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Napoleon (Google-style from docstrings_comments.md)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_examples = True

# Intersphinx
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Type hints (conventions in type_hints.md)
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True
```

## .readthedocs.yaml

```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"
  jobs:
    post_install:
      - pip install -e .

sphinx:
  configuration: docs/source/conf.py
  fail_on_warning: false

python:
  install:
    - requirements: docs/requirements.txt
    - method: pip
      path: .
      extra_requirements:
        - docs

formats:
  - pdf
  - epub
```

## docs/requirements.txt

```
sphinx>=7.0
pydata-sphinx-theme>=0.14
sphinx-autodoc-typehints>=1.24
sphinx-copybutton>=0.5
myst-parser>=2.0.0
```

**Important**: Keep `docs/requirements.txt` synchronized with `pyproject.toml`'s `[project.optional-dependencies]` docs extra. This ensures:
- Local development: `pip install -e ".[docs]"`
- Read the Docs: Uses `extra_requirements: [docs]` from `.readthedocs.yaml`
- CI/CD: Can reference either file consistently

Example `pyproject.toml`:
```toml
[project.optional-dependencies]
docs = [
    "sphinx",
    "pydata-sphinx-theme",
    "sphinx-autodoc-typehints",
    "sphinx-copybutton",
    "myst-parser"
]
```

## Testing Documentation

### Pre-commit
```bash
sphinx-build -b html -W --keep-going docs/source docs/build
sphinx-build -b linkcheck docs/source docs/build
pytest --doctest-modules
```

### CI Integration
```yaml
- name: Build documentation
  run: |
    pip install -e ".[docs]"
    cd docs
    make html SPHINXOPTS="-W --keep-going"
```

## Content Guidelines

### Index Page (from README.md)
1. Project tagline (1 sentence)
2. Key features (3-5 bullets)
3. Quick example (5-10 lines)
4. Installation command
5. Table of contents

### User Guide Organization
- Organize by user goals/tasks
- Start with common use cases
- Complete, runnable examples
- Explain "how" and "why"

### API Reference
- Auto-generate with `automodule`/`autosummary`
- Group by module/functionality
- Include inheritance diagrams
- Cross-reference related items

## Maintenance Checklist

### After Any Documentation Changes
- [ ] **Rebuild docs locally** to validate the build process works:
  ```bash
  cd docs && make clean && make html
  ```
- [ ] Test docs build without warnings:
  ```bash
  sphinx-build -b html -W --keep-going docs/source docs/build
  ```
- [ ] Verify the output in `docs/build/html/index.html` renders correctly

### Each Release
- [ ] Update version (auto from `__version__`)
- [ ] Keep README.md and readthedocs documentation in sync
- [ ] Update code examples
- [ ] Test docs build without warnings
- [ ] Check for broken links

### Quarterly
- [ ] Review analytics for confusing sections
- [ ] Update installation instructions
- [ ] Refresh examples
- [ ] Review documentation issues

## Component Documentation Templates

### Template for Mixins and Metaclasses

Copy this template when creating documentation for a new mixin or metaclass:
```rst
ComponentName
=============

.. autoclass:: mixinforge.ComponentName
   :members:
   :special-members: __init__

Use Cases
---------

When to use:
* Specific scenario 1
* Specific scenario 2

Example::

    from mixinforge import ComponentName

    class MyClass(ComponentName):
        def __init__(self):
            super().__init__()

Thread Safety / Caveats
------------------------

See :ref:`thread-safety` for considerations.
```

### Template for Utility Functions

Copy this template when creating documentation for a new utility function:
```rst
function_name
=============

.. autofunction:: mixinforge.function_name

Use Cases
---------

When to use:
* Specific scenario 1
* Specific scenario 2

Example::

    from mixinforge import function_name

    result = function_name(input_data)
    # Expected output...

Notes
-----

Performance considerations, edge cases, or related functions.
```

### Key Areas
1. **ParameterizableMixin**: Parameter management, JSON serialization
2. **CacheablePropertiesMixin**: Cache discovery and invalidation
3. **SingleThreadEnforcerMixin**: Thread safety patterns
4. **GuardedInitMeta**: Initialization lifecycle (metaclass)
5. **SingletonMixin**: Single-instance pattern enforcement
6. **NotPicklableMixin**: Serialization constraints
7. **Utility functions**: `dumpjs`, `loadjs`, `update_jsparams`, `access_jsparams`, `sort_dict_by_keys`

---

## Version Management

The documentation version is automatically extracted from the package:

```python
# In conf.py
from mixinforge import __version__
version = release = __version__
```

This ensures docs always match the installed package version. Update version only in:
- `pyproject.toml` (for the package)
- `src/mixinforge/_version_info.py` (if using separate version file)

**Never hardcode version numbers in `conf.py`.**
