# mixinforge
[![PyPI version](https://img.shields.io/pypi/v/mixinforge.svg)](https://pypi.org/project/mixinforge/)
[![Python versions](https://img.shields.io/pypi/pyversions/mixinforge.svg)](https://pypi.org/project/mixinforge/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/pythagoras-dev/mixinforge/blob/master/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/mixinforge?color=blue)](https://pypistats.org/packages/mixinforge)
[![Documentation Status](https://app.readthedocs.org/projects/mixinforge/badge/?version=latest)](https://mixinforge.readthedocs.io/en/latest/)
[![Code style: pep8](https://img.shields.io/badge/code_style-pep8-blue.svg)](https://peps.python.org/pep-0008/)
[![Docstring Style: Google](https://img.shields.io/badge/docstrings_style-Google-blue)](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)

A collection of Python mixins and utilities for building robust, configurable classes.

## What Is It?

`mixinforge` is a lightweight library providing reusable mixins and utility functions that help you build well-structured Python classes. It offers tools for:

- **Parameter management** — Track, serialize, and deserialize class configuration parameters
- **Cache management** — Automatically discover and invalidate `cached_property` attributes
- **Initialization control** — Enforce strict initialization contracts with lifecycle hooks
- **Thread safety** — Enforce single-threaded execution with multi-process support
- **Singleton pattern** — Ensure each subclass maintains exactly one instance
- **Pickle prevention** — Explicitly prevent objects from being pickled when serialization is unsafe
- **JSON serialization** — Convert objects and parameters to/from portable JSON representations
- **Dictionary utilities** — Helper functions for consistent dictionary handling

## Quick Example

Here's a quick example demonstrating parameter management and JSON serialization:

```python
from mixinforge import ParameterizableMixin, dumpjs, loadjs

class MyModel(ParameterizableMixin):
    def __init__(self, n_trees=10, depth=3):
        self.n_trees = n_trees
        self.depth = depth

    def get_params(self) -> dict:
        return {"n_trees": self.n_trees, "depth": self.depth}

# Create and configure
model = MyModel(n_trees=50, depth=5)

# Serialize to JSON
js = dumpjs(model)

# Recreate from JSON
model2 = loadjs(js)
assert model2.get_params() == model.get_params()
```

## Installation

The source code is hosted on GitHub at:
[https://github.com/pythagoras-dev/mixinforge](https://github.com/pythagoras-dev/mixinforge)

Binary installers for the latest released version are available at the Python package index at:
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

## Available Mixins and Metaclasses

### ParameterizableMixin

A base class for objects with configuration parameters. Enables standardized parameter access, JSON serialization, and distinguishes between essential and auxiliary parameters.

```python
from mixinforge import ParameterizableMixin, dumpjs, loadjs


class MyModel(ParameterizableMixin):
    def __init__(self, n_trees=10, depth=3, verbose=False):
        self.n_trees = n_trees
        self.depth = depth
        self.verbose = verbose

    def get_params(self) -> dict:
        return {"n_trees": self.n_trees, "depth": self.depth, "verbose": self.verbose}

    @property
    def essential_param_names(self) -> set[str]:
        return {"n_trees", "depth"}  # verbose is auxiliary


model = MyModel(n_trees=50, depth=5, verbose=True)

# Get parameters
model.get_params()              # {"n_trees": 50, "depth": 5, "verbose": True}
model.get_essential_params()    # {"n_trees": 50, "depth": 5}
model.get_auxiliary_params()    # {"verbose": True}

# Serialize to JSON
js = dumpjs(model)

# Recreate from JSON
model2 = loadjs(js)
assert model2.get_params() == model.get_params()
```

### CacheablePropertiesMixin

A mixin for managing `functools.cached_property` attributes with automatic discovery and invalidation across the class hierarchy.

```python
from functools import cached_property
from mixinforge import CacheablePropertiesMixin


class DataProcessor(CacheablePropertiesMixin):
    def __init__(self, data):
        self._data = data

    @cached_property
    def processed(self):
        print("Processing...")
        return [x * 2 for x in self._data]

    @cached_property
    def summary(self):
        return sum(self.processed)


processor = DataProcessor([1, 2, 3])

# Check cache status
processor._get_all_cached_properties_status()  # {"processed": False, "summary": False}

# Access triggers caching
_ = processor.processed  # prints "Processing..."
processor._get_all_cached_properties_status()  # {"processed": True, "summary": False}

# Invalidate all caches
processor._invalidate_cache()
processor._get_all_cached_properties_status()  # {"processed": False, "summary": False}
```

### NotPicklableMixin

A mixin that explicitly prevents objects from being pickled or unpickled. Useful for objects that hold non-serializable resources like database connections, file handles, or network sockets.

```python
import pickle
from mixinforge import NotPicklableMixin


class DatabaseConnection(NotPicklableMixin):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        # ... establish connection


conn = DatabaseConnection("postgresql://localhost/mydb")

# Any attempt to pickle raises TypeError
try:
    pickle.dumps(conn)
except TypeError as e:
    print(e)  # "Pickling is not allowed for DatabaseConnection objects"
```

### GuardedInitMeta

A metaclass that enforces strict initialization control and provides lifecycle hooks. It ensures that `_init_finished` is `False` during `__init__` and automatically sets it to `True` afterward, enabling reliable initialization state checks.

```python
from mixinforge import GuardedInitMeta


class MyService(metaclass=GuardedInitMeta):
    def __init__(self, name):
        self._init_finished = False  # Required by the contract
        self.name = name
        # _init_finished is automatically set to True after __init__

    def __post_init__(self):
        # Optional hook called after initialization completes
        print(f"Service '{self.name}' initialized")


service = MyService("worker")  # prints "Service 'worker' initialized"
print(service._init_finished)  # True
```

### SingleThreadEnforcerMixin

A mixin to enforce single-threaded execution with multi-process support. Ensures methods are called only from the thread that first instantiated the object, while automatically supporting process-based parallelism through fork detection.

```python
from mixinforge import SingleThreadEnforcerMixin


class MyProcessor(SingleThreadEnforcerMixin):
    def __init__(self):
        super().__init__()
        self.data = []

    def process(self, item):
        self.restrict_to_single_thread()
        self.data.append(item)
        return item * 2


processor = MyProcessor()
processor.process(5)  # Works on the owner thread

# Calling from a different thread raises RuntimeError
```

## CLI Commands

mixinforge provides command-line tools for project analysis and maintenance.

### mf-get-stats

Generate project metrics and save to file:

```bash
# Analyze current directory
mf-get-stats

# Analyze specific directory
mf-get-stats /path/to/project

# Specify custom output filename
mf-get-stats --output my_metrics.md
```

Generates a markdown report with code statistics including lines of code (LOC), source lines of code (SLOC), class counts, function counts, and file counts, broken down by main code and unit tests. Also displays a formatted summary table in the console.

### mf-clean-cache

Remove Python cache files from a directory and its subdirectories:

```bash
# Clean current directory
mf-clean-cache

# Clean specific directory
mf-clean-cache /path/to/project

# Specify custom report filename
mf-clean-cache --output cleanup_report.md
```

Removes `__pycache__` directories, `.pyc` files, `.pyo` files, and cache directories from pytest, mypy, ruff, hypothesis, tox, and coverage tools. Generates a detailed markdown report of removed items.

## Utility Functions

### JSON Serialization

```python
from mixinforge import ParameterizableMixin, dumpjs, loadjs, update_jsparams, access_jsparams


class MyModel(ParameterizableMixin):
    def __init__(self, n_trees=10, depth=3):
        self.n_trees = n_trees
        self.depth = depth

    def get_params(self) -> dict:
        return {"n_trees": self.n_trees, "depth": self.depth}


model = MyModel(n_trees=50, depth=5)

# Serialize an object to JSON
js = dumpjs(model)

# Deserialize back to an object
model2 = loadjs(js)

# Update parameters in JSON without full deserialization
js_updated = update_jsparams(js, n_trees=100)

# Access specific parameters from JSON
subset = access_jsparams(js, "n_trees", "depth")  # {"n_trees": 50, "depth": 5}
```

### Dictionary Sorting

```python
from mixinforge import sort_dict_by_keys

# Sort dictionary keys alphabetically
sorted_dict = sort_dict_by_keys({"zebra": 1, "apple": 2, "mango": 3})
# {"apple": 2, "mango": 3, "zebra": 1}
```

## API Reference

### Mixins

| Mixin | Description |
|-------|-------------|
| `ParameterizableMixin` | Base class for parameterizable objects with JSON serialization support |
| `CacheablePropertiesMixin` | Automatic discovery and invalidation of `cached_property` attributes |
| `NotPicklableMixin` | Prevents pickling/unpickling of objects |
| `SingleThreadEnforcerMixin` | Enforces single-threaded execution with multi-process support |
| `SingletonMixin` | Ensures each subclass maintains exactly one instance |

### Metaclasses

| Metaclass | Description |
|-----------|-------------|
| `GuardedInitMeta` | Metaclass for strict initialization control and lifecycle hooks (`__post_init__`, `__post_setstate__`) |

### Functions

| Function | Description |
|----------|-------------|
| `dumpjs(obj)` | Serialize an object to a JSON string |
| `loadjs(js)` | Deserialize a JSON string back to an object |
| `update_jsparams(js, **updates)` | Update parameters in a JSON string without full deserialization |
| `access_jsparams(js, *names)` | Extract specific parameters from a JSON string |
| `sort_dict_by_keys(d)` | Return a new dictionary with keys sorted alphabetically |

### Types

| Type | Description |
|------|-------------|
| `JsonSerializedObject` | Type alias for JSON strings produced by `dumpjs` |

## Project Statistics

<!-- STATS_START -->
| Metric | Main code | Unit Tests | Total |
|--------|-----------|------------|-------|
| Lines Of Code (LOC) | 2935 | 4797 | 7732 |
| Source Lines Of Code (SLOC) | 1284 | 2974 | 4258 |
| Classes | 13 | 105 | 118 |
| Functions / Methods | 93 | 447 | 540 |
| Files | 15 | 34 | 49 |
<!-- STATS_END -->

## Development

- Run tests:
  - With pytest: `pytest`
  - Or via Python: `python -m pytest`
- Supported Python versions: 3.11+
- See contributing guidelines: [contributing.md](https://github.com/pythagoras-dev/mixinforge/blob/master/CONTRIBUTING.md)
- See docstrings and comments guidelines: [docstrings_comments.md](https://github.com/pythagoras-dev/mixinforge/blob/master/docstrings_comments.md)
- See type hints guidelines: [type_hints.md](https://github.com/pythagoras-dev/mixinforge/blob/master/type_hints.md)
- See Read the Docs configuration guide: [readthedocs.md](https://github.com/pythagoras-dev/mixinforge/blob/master/readthedocs.md)

## License

This project is licensed under the MIT License — see [LICENSE](https://github.com/pythagoras-dev/mixinforge/blob/master/LICENSE) for details.

## Key Contacts

* [Vlad (Volodymyr) Pavlov](https://www.linkedin.com/in/vlpavlov/)
