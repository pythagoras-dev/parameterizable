# mixinforge
[![PyPI version](https://img.shields.io/pypi/v/mixinforge.svg?color=green)](https://pypi.org/project/mixinforge/)
[![Python versions](https://img.shields.io/pypi/pyversions/mixinforge.svg)](https://github.com/pythagoras-dev/mixinforge)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/pythagoras-dev/mixinforge/blob/master/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/mixinforge?color=blue)](https://pypistats.org/packages/mixinforge)
[![Documentation Status](https://app.readthedocs.org/projects/mixinforge/badge/?version=latest)](https://mixinforge.readthedocs.io/en/latest/)
[![Code style: pep8](https://img.shields.io/badge/code_style-pep8-blue.svg)](https://peps.python.org/pep-0008/)
[![Docstring Style: Google](https://img.shields.io/badge/docstrings_style-Google-blue)](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)

A collection of Python mixins, metaclasses, utility functions, and CLI
tools for building robust, configurable classes.

## What Is It?

`mixinforge` is a lightweight library providing three key areas of
functionality:

1. **Mixins & Metaclasses** — Reusable components for parameter
   management, cache control, initialization contracts, thread safety,
   singleton pattern, and pickle prevention
2. **Utility Functions** — Tools for JSON serialization, nested
   collection processing, and dictionary operations
3. **CLI Tools** — Command-line utilities for project analysis and
   maintenance

## Quick Example

Here's an example showing thread safety enforcement:

```python
from mixinforge import SingleThreadEnforcerMixin

class DatabaseConnection(SingleThreadEnforcerMixin):
    def __init__(self, connection_string: str):
        super().__init__()
        self.connection_string = connection_string
        self.connection = self._connect()

    def _connect(self):
        return f"Connected to {self.connection_string}"

    def query(self, sql: str):
        self._restrict_to_single_thread()  # Enforces thread safety
        return f"Executing: {sql}"

# Works fine on the owner thread
db = DatabaseConnection("localhost:5432")
result = db.query("SELECT * FROM users")

# Calling from another thread raises RuntimeError
import threading
threading.Thread(
    target=lambda: db.query("SELECT *")
).start()  # Raises RuntimeError!
```

## Installation

The source code is hosted on GitHub at:
[https://github.com/pythagoras-dev/mixinforge](https://github.com/pythagoras-dev/mixinforge)

Binary installers for the latest released version are available at the
Python package index at:
[https://pypi.org/project/mixinforge](https://pypi.org/project/mixinforge)

Using uv:
```bash
uv add mixinforge
```

Using pip:
```bash
pip install mixinforge
```

## Requirements

- Python >= 3.11
- Runtime dependencies:
  - tabulate

For development:
- pytest (optional)

## API Overview

### Mixins & Metaclasses

| Component | Description |
|-----------|-------------|
| `ParameterizableMixin` | Base class for parameterizable objects with JSON serialization |
| `CacheablePropertiesMixin` | Auto discovery and invalidation of `cached_property` |
| `NotPicklableMixin` | Prevents pickling/unpickling of objects |
| `GuardedInitMeta` | Strict initialization control with lifecycle hooks |
| `SingleThreadEnforcerMixin` | Enforces single-threaded execution |
| `SingletonMixin` | Ensures each subclass has exactly one instance |

### Utility Functions

| Function | Description |
|----------|-------------|
| `dumpjs(obj)` | Serialize object to JSON string |
| `loadjs(js)` | Deserialize JSON string to object |
| `update_jsparams(js, **updates)` | Update params in JSON |
| `access_jsparams(js, *names)` | Extract params from JSON |
| `sort_dict_by_keys(d)` | Sort dictionary keys alphabetically |
| `find_atomics_in_nested_collections(obj)` | Find atomics in nested collections |
| `find_nonatomics_inside_composite_object(obj, type)` | Find instances of type in composite |

### CLI Tools

| Command | Description |
|---------|-------------|
| `mf-get-stats` | Analyze project metrics and generate reports |
| `mf-clear-cache` | Remove Python cache files and directories |

## Mixins & Metaclasses

### ParameterizableMixin

A base class for objects with configuration parameters. Enables
standardized parameter access and JSON serialization.

**Key features:**
- `get_params()` — Returns all parameters as a dictionary
- `get_default_params()` — Class method to get default parameter
  values from `__init__` signature
- `get_essential_params()` — Returns only essential configuration
  parameters
- `get_auxiliary_params()` — Returns auxiliary parameters (logging,
  verbosity, etc.)
- `essential_param_names` — Property to specify which parameters are
  core to the object's identity
- `get_jsparams()` — Get parameters as JSON string
- `get_essential_jsparams()` / `get_auxiliary_jsparams()` — Get
  filtered parameters as JSON
- Works seamlessly with `dumpjs()` and `loadjs()` for full object
  serialization

### CacheablePropertiesMixin

A mixin for managing `functools.cached_property` attributes with
automatic discovery and invalidation across the class hierarchy.

**Key methods:**
- `_get_all_cached_properties_status()` — Check which cached
  properties are currently cached (returns dict)
- `_get_cached_property_status(name)` — Check if a specific property
  is cached
- `_get_all_cached_properties()` — Retrieve all currently cached
  values
- `_get_cached_property(name)` — Get a specific cached value
- `_set_cached_properties(**kwargs)` — Manually set cached values
  (useful for testing/restoration)
- `_invalidate_cache()` — Clear all cached properties across the
  entire class hierarchy
- `_all_cached_properties_names` — Property returning all cached
  property names

Automatically discovers cached properties from all classes in the MRO,
including decorator-wrapped properties, making it reliable for complex
inheritance structures.

### NotPicklableMixin

A mixin that explicitly prevents objects from being pickled or
unpickled. Useful for objects that hold non-serializable resources like
database connections, file handles, or network sockets.

Raises `TypeError` on any pickling attempt, providing clear error
messages about why serialization is blocked.

### GuardedInitMeta

A metaclass that enforces strict initialization control and provides
lifecycle hooks. It ensures that `_init_finished` is `False` during
`__init__` and automatically sets it to `True` afterward, enabling
reliable initialization state checks.

**Key features:**
- Automatic `_init_finished` flag management (False during init, True
  after)
- `__post_init__()` hook — Called automatically after `__init__`
  completes
- `__post_setstate__()` hook — Called after unpickling when restoring
  object state
- Automatic `__setstate__` wrapping for proper unpickling behavior
- Validates `_init_finished=False` in pickled state to prevent
  corruption
- Compatible with `ABCMeta` for abstract base classes
- Prevents use with dataclasses (incompatible)
- Validates single GuardedInitMeta base in multiple inheritance

Enforces initialization contracts and provides clear error messages when
contracts are violated, making initialization bugs easier to catch.

### SingleThreadEnforcerMixin

A mixin to enforce single-threaded execution with multi-process support.
Ensures methods are called only from the thread that first instantiated
the object, while automatically supporting process-based parallelism
through fork detection.

**Key method:**
- `_restrict_to_single_thread()` — Call this at the start of methods
  that need thread enforcement

Automatically detects process forks and resets ownership, making it safe
for multiprocessing workflows.

### SingletonMixin

A mixin for implementing the singleton pattern. Ensures each subclass
maintains exactly one instance that is returned on every instantiation
attempt.

Useful for classes that should have only a single instance throughout
the application lifetime, such as configuration managers or resource
coordinators. Each subclass gets its own singleton instance.

## Utility Functions

### JSON Serialization

mixinforge provides a complete JSON serialization system for Python
objects:

- **`dumpjs(obj)`** — Serialize any Python object (including classes,
  instances, nested structures) to a JSON string
- **`loadjs(js)`** — Deserialize a JSON string back to its original
  Python object
- **`update_jsparams(js, **kwargs)`** — Modify parameters in serialized
  JSON without full deserialization
- **`access_jsparams(js, *names)`** — Extract specific parameters from
  serialized JSON

This system handles complex objects including class hierarchies,
`__slots__`, nested collections, and maintains object identity; it
seamlessly integrates with `ParameterizableMixin`.

### Nested Collection Processing

Tools for working with nested data structures:

- **`find_atomics_in_nested_collections(obj)`** — Recursively find all
  atomic-type objects (primitives, strings, etc.) within nested
  collections (returns iterator)
- **`find_nonatomics_inside_composite_object(obj, target_type)`** —
  Recursively find all instances of a specific non-atomic type within
  composite structures (returns iterator)

These functions handle arbitrary nesting depths and complex object
graphs, useful for introspection and validation.

### Dictionary Utilities

- **`sort_dict_by_keys(d)`** — Returns a new dictionary with keys
  sorted alphabetically, useful for consistent serialization and
  comparison

## CLI Tools

mixinforge provides two command-line tools for project analysis and
maintenance.

### mf-get-stats

Analyzes Python projects and generates comprehensive code metrics.

**Usage:**
```bash
# Analyze current directory
mf-get-stats

# Analyze specific directory
mf-get-stats /path/to/project

# Specify custom output filename
mf-get-stats --output my_metrics.md
```

**Features:**
- Generates markdown report with detailed statistics:
  - Lines of Code (LOC) and Source Lines of Code (SLOC)
  - Class and function counts
  - File counts
  - Breakdown by main code vs. unit tests
- Displays formatted summary table in console
- Auto-updates `README.md` and Sphinx documentation if special markers
  are present:
  - `<!-- MIXINFORGE_STATS_START -->` and `<!-- MIXINFORGE_STATS_END -->` for markdown
  - `.. MIXINFORGE_STATS_START` and `.. MIXINFORGE_STATS_END` for
    reStructuredText
- Returns list of updated files for CI/CD integration

This tool is ideal for tracking project growth, maintaining
documentation, and integrating metrics into automated workflows.

### mf-clear-cache

Removes all Python cache files and directories from a project.

**Usage:**
```bash
# Clean current directory
mf-clear-cache

# Clean specific directory
mf-clear-cache /path/to/project

# Specify custom report filename
mf-clear-cache --output cleanup_report.md
```

**What it removes:**
- `__pycache__` directories
- `.pyc` and `.pyo` compiled bytecode files
- Cache directories from:
  - pytest (`.pytest_cache`)
  - mypy (`.mypy_cache`)
  - ruff (`.ruff_cache`)
  - hypothesis (`.hypothesis`)
  - tox (`.tox`)
  - coverage (`.coverage`, `htmlcov`)

Generates a detailed markdown report categorizing removed items. Useful
for cleaning build artifacts before commits or releases.

## Project Statistics

<!-- MIXINFORGE_STATS_START -->
| Metric | Main code | Unit Tests | Total |
|--------|-----------|------------|-------|
| Lines Of Code (LOC) | 3331 | 7379 | 10710 |
| Source Lines Of Code (SLOC) | 1482 | 4374 | 5856 |
| Classes | 13 | 142 | 155 |
| Functions / Methods | 100 | 637 | 737 |
| Files | 15 | 51 | 66 |
<!-- MIXINFORGE_STATS_END -->

## Development

- Run tests:
  - With pytest: `pytest`
  - Or via Python: `python -m pytest`
- Supported Python versions: 3.11+
- See contributing guidelines:
  [contributing.md](https://github.com/pythagoras-dev/mixinforge/blob/master/CONTRIBUTING.md)
- See docstrings and comments guidelines:
  [docstrings_comments.md](https://github.com/pythagoras-dev/mixinforge/blob/master/docstrings_comments.md)
- See type hints guidelines:
  [type_hints.md](https://github.com/pythagoras-dev/mixinforge/blob/master/type_hints.md)
- See Read the Docs configuration guide:
  [readthedocs.md](https://github.com/pythagoras-dev/mixinforge/blob/master/readthedocs.md)

## License

This project is licensed under the MIT License — see
[LICENSE](https://github.com/pythagoras-dev/mixinforge/blob/master/LICENSE)
for details.

## Contact

* **Maintainer**: [Vlad (Volodymyr) Pavlov](https://www.linkedin.com/in/vlpavlov/)
* **Email**: vlpavlov@ieee.org
