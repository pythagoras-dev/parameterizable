# parameterizable

Parameter manipulation for Python classes.

## What Is It?

`parameterizable` provides functionality for work with parameterizable 
classes: those that have (hyper) parameters which define object's configuration,
that is different from the object's internal contents or data. Such parameters 
are typically passed to the `.__init__()` method when an object is created.

`parameterizable` allows to:
* Get parameters of an object as a dictionary.
* Get default parameters of a class as a dictionary.
* Serialize an object's parameters to a JSON string. 
* Recreate the object from its parameters, stored in a JSON string.

## Why Is It Useful?

`parameterizable` is useful for developers working with 
configurable Python objects, especially in scenarios involving 
machine learning, scientific computing, or any domain where 
object's behavior is defined by the object's parameters. It provides:

* **Consistency**: Ensures a standardized way to handle parameters 
across different classes.
* **Serialization**: Simplifies saving and loading configuration-defined objects
using JSON.
* **Reproducibility**: Facilitates recreating objects with the same configuration, 
which is critical for debugging and sharing experiments.

By abstracting parameter handling, this library reduces boilerplate code 
and improves maintainability.

## Usage

Most users will:
- Inherit from `ParameterizableClass` in their own classes, 
- Implement the `.get_params()` method to expose the configuration needed to recreate the object, and (sometimes)
- Implement the `.essential_param_names` property to expose the core parameters which determine the object's behavior.


## Key Classes, Methods and Functions,

- `ParameterizableClass`: Base class for parameterizable objects. Derive your class from it to enable the library’s features.
- `NotPicklableClass`: Mixin that prevents pickling/unpickling; inherit from it to make your class explicitly non-picklable.
- `JsonSerializedObject`: A string containing JSON-serialized object.
- `ParameterizableClass.get_params()`: Implement in your subclass to return the configuration dictionary 
needed to recreate the object.
- `ParameterizableClass.get_default_params()`: Class method returning default parameters for the class as a dictionary.
- `ParameterizableClass.essential_param_names`: Implement in your subclass to return the names of the core parameters
which determine the object's behavior. If not implemented, all parameters are considered essential.
- `ParameterizableClass.auxiliary_param_names`: A property that returns the names of the auxiliary parameters.
- `ParameterizableClass.get_jsparams()`: A method that serializes an object's parameters 
to a JSON string (`JsonSerializedObject`).
- `ParameterizableClass.get_essential_jsparams()`: A method that returns a JSON string with essential parameters only.
- `ParameterizableClass.get_auxiliary_jsparams()`: A method that returns a JSON string with auxiliary parameters only.
- `ParameterizableClass.get_default_jsparams()`: Class method returning default parameters for the class as a JSON string.
- `dumpjs(obj)`: Return a JSON string representation of an object.
- `loadjs(js)`: Return an object from a JSON string.
- `update_jsparams(js, updates)`: Return a new JSON string with selected parameters updated without full deserialization.
- `access_jsparams(js, names)`: Return a dict with a subset of params, stored inside a JSON string.
- `sort_dict_by_keys(d)`: Utility to produce a new dict whose keys are sorted alphabetically.

## How To Get It?

The source code is hosted on GitHub at:
[https://github.com/pythagoras-dev/parameterizable](https://github.com/pythagoras-dev/parameterizable) 

Binary installers for the latest released version are available at the Python package index at:
[https://pypi.org/project/parameterizable](https://pypi.org/project/parameterizable)

Using uv :
```
uv add parameterizable
```

Using pip (legacy alternative to uv):
```
pip install parameterizable
```

## Requirements

- Python >= 3.10
- Runtime dependencies: none

For development:
- pytest (optional)

## Quick Start

Here's a minimal example showing how to make your class parameterizable and serialize/deserialize it:

```python
from parameterizable.parameterizable import ParameterizableClass
from parameterizable.json_processor import dumpjs, loadjs

class MyModel(ParameterizableClass):
    def __init__(self, n_trees=10, depth=3, verbose=False):
        self.n_trees = n_trees
        self.depth = depth
        self.verbose = verbose

    def get_params(self) -> dict:
        # Only values returned here are considered this object's "parameters"
        return {"n_trees": self.n_trees, "depth": self.depth, "verbose": self.verbose}

    # Optional: list the parameters that define identity/behavior
    @property
    def essential_param_names(self) -> set[str]:
        return {"n_trees", "depth"}

m = MyModel(n_trees=50, depth=5, verbose=True)

# Serialize parameters to JSON
js = dumpjs(m)

# Recreate an equivalent object from JSON
m2 = loadjs(js)
assert isinstance(m2, MyModel)
assert m2.get_params() == m.get_params()
```

## API Examples

- Update parameters in JSON without full deserialization:

```python
from parameterizable.json_processor import update_jsparams, dumpjs, loadjs

js2 = update_jsparams(js, n_trees=100)  # returns a new JSON string
m3 = loadjs(js2)
assert m3.n_trees == 100
```

- Access a subset of parameters directly from JSON:

```python
from parameterizable.json_processor import access_jsparams

subset = access_jsparams(js2, "n_trees", "depth")
assert subset == {"n_trees": 100, "depth": 5}
```

- Work with essential/auxiliary parameters:

```python
m.get_essential_params()      # {"n_trees": 50, "depth": 5}
m.get_essential_jsparams()    # JSON string with only essential params
m.get_auxiliary_params()      # {"verbose": True}
m.get_auxiliary_jsparams()    # JSON string with only auxiliary params
```

- Sort dictionaries by keys (utility):

```python
from parameterizable.dict_sorter import sort_dict_by_keys
sort_dict_by_keys({"b": 2, "a": 1})  # {"a": 1, "b": 2}
```

- Prevent pickling/unpickling using NotPicklableClass:

```python
import pickle
from parameterizable import NotPicklableClass

class Connection(NotPicklableClass):
    pass

conn = Connection()

# Any attempt to pickle or unpickle will raise TypeError
try:
    pickle.dumps(conn)
except TypeError:
    print("Connection cannot be pickled")
```

## Development

- Run tests:
  - With pytest: `pytest`
  - Or via Python: `python -m pytest`
- Supported Python versions: 3.10+
- See contributing guidelines: [contributing.md](contributing.md)

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Key Contacts

* [Vlad (Volodymyr) Pavlov](https://www.linkedin.com/in/vlpavlov/)
