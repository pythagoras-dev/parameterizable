# mixinforge
[![PyPI version](https://img.shields.io/pypi/v/mixinforge.svg)](https://pypi.org/project/mixinforge/)
[![Python versions](https://img.shields.io/pypi/pyversions/mixinforge.svg)](https://pypi.org/project/mixinforge/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/mixinforge?color=blue)](https://pypistats.org/packages/mixinforge)
[![Documentation Status](https://app.readthedocs.org/projects/mixinforge/badge/?version=latest)](https://mixinforge.readthedocs.io/en/latest/)
[![Code style: pep8](https://img.shields.io/badge/code_style-pep8-blue.svg)](https://peps.python.org/pep-0008/)
[![Docstring Style: Google](https://img.shields.io/badge/docstrings_style-Google-blue)](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)

A collection of Python mixins and utilities for building robust, configurable classes.

## What Is It?

`mixinforge` is a lightweight library providing reusable mixins and utility functions that help you build well-structured Python classes. It offers tools for:

- **Parameter management** — Track, serialize, and deserialize class configuration parameters
- **Cache management** — Automatically discover and invalidate `cached_property` attributes
- **Pickle prevention** — Explicitly prevent objects from being pickled when serialization is unsafe
- **JSON serialization** — Convert objects and parameters to/from portable JSON representations
- **Dictionary utilities** — Helper functions for consistent dictionary handling

## Available Mixins

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

## Utility Functions

### JSON Serialization

```python
from mixinforge import dumpjs, loadjs, update_jsparams, access_jsparams

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

## Installation

The source code is hosted on GitHub at:
[https://github.com/pythagoras-dev/mixinforge](https://github.com/pythagoras-dev/mixinforge)

Binary installers for the latest released version are available at the Python package index at:
[https://pypi.org/project/mixinforge](https://pypi.org/project/mixinforge)

Using uv:
```
uv add mixinforge
```

Using pip:
```
pip install mixinforge
```

## Requirements

- Python >= 3.11
- Runtime dependencies: none

For development:
- pytest (optional)

## API Reference

### Mixins

| Mixin | Description |
|-------|-------------|
| `ParameterizableMixin` | Base class for parameterizable objects with JSON serialization support |
| `CacheablePropertiesMixin` | Automatic discovery and invalidation of `cached_property` attributes |
| `NotPicklableMixin` | Prevents pickling/unpickling of objects |

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

## Development

- Run tests:
  - With pytest: `pytest`
  - Or via Python: `python -m pytest`
- Supported Python versions: 3.11+
- See contributing guidelines: [contributing.md](contributing.md)

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Key Contacts

* [Vlad (Volodymyr) Pavlov](https://www.linkedin.com/in/vlpavlov/)
