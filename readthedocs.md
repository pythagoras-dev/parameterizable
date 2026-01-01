# Read the Docs Configuration Guide

> **References**:
> - Docstring formatting: [docstrings_comments.md](docstrings_comments.md)
> - Type hints: [type_hints.md](type_hints.md)
> - Contribution workflow: [contributing.md](contributing.md)
> - Project structure: [README.md](README.md)

## Documentation Structure

```
docs/
├── source/
│   ├── conf.py
│   ├── index.rst
│   ├── installation.rst
│   ├── quickstart.rst
│   ├── user_guide/
│   │   ├── index.rst
│   │   ├── parameterizable.rst
│   │   ├── cacheable_properties.rst
│   │   ├── thread_safety.rst
│   │   └── advanced_usage.rst
│   ├── api_reference/
│   │   ├── index.rst
│   │   └── modules.rst
│   └── changelog.rst
└── requirements.txt
```

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
```

## Changelog Format

Use Keep a Changelog format with commit prefixes from contributing.md:

```rst
Changelog
=========

Version 0.202.0 (2026-01-01)
----------------------------

Added
~~~~~
- ENH: New SingletonMixin feature

Changed
~~~~~~~
- REF: Refactored cache invalidation

Deprecated
~~~~~~~~~~
- old_function() will be removed in 0.300.0

Fixed
~~~~~
- BUG: Fixed thread safety issue
```

### Version Directives

```rst
.. deprecated:: 0.202.0
   Use :func:`new_function` instead.

.. versionadded:: 0.202.0
   New feature description.

.. versionchanged:: 0.202.0
   Behavior change description.
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

### Each Release
- [ ] Update version (auto from `__version__`)
- [ ] Add changelog entry (use contributing.md prefixes)
- [ ] Update code examples
- [ ] Test docs build without warnings
- [ ] Check for broken links

### Quarterly
- [ ] Review analytics for confusing sections
- [ ] Update installation instructions
- [ ] Refresh examples
- [ ] Review documentation issues

## Project-Specific: Mixins Documentation

### Structure for Each Mixin
```rst
MixinName
=========

.. autoclass:: mixinforge.MixinName
   :members:
   :special-members: __init__

Use Cases
---------

When to use:
* Specific scenario 1
* Specific scenario 2

Example::

    from mixinforge import MixinName

    class MyClass(MixinName):
        def __init__(self):
            super().__init__()

Thread Safety / Caveats
------------------------

See :ref:`thread-safety` for considerations.
```

### Key Areas
1. **ParameterizableMixin**: Parameter management, JSON serialization
2. **CacheablePropertiesMixin**: Cache discovery and invalidation
3. **SingleThreadEnforcerMixin**: Thread safety patterns
4. **GuardedInitMeta**: Initialization lifecycle
5. **NotPicklableMixin**: Serialization constraints
