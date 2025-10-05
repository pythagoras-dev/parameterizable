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
- Inherit from `ParameterizableClass` in their own classes, and
- Implement the `.get_params()` method to expose the configuration needed to recreate the object.


## Key Classes, Functions, and Constants

- ParameterizableClass: Base class for parameterizable objects. Derive your class from it to enable the library’s features.
- ParameterizableClass.get_params(): Implement in your subclass to return the configuration dictionary needed to recreate the object.
- ParameterizableClass.get_default_params(): Class method returning default parameters for the class as a dictionary.
- dumps(obj): Serialize an object's parameters to a JSON string (portable format with sorted keys).
- loads(js): Deserialize a JSON string back into an object of the original class.
- update_jsparams(js, updates): Return a new JSON string with selected parameters updated without full deserialization.
- access_jsparams(js): Provide a JsonSerializedParams (dict-like) view to inspect parameters inside the JSON string.
- JsonSerializedParams: A string containing JSON-serialized parameters.
- sort_dict_by_keys(d): Utility to produce a new dict whose keys are sorted alphabetically.

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

## Key Contacts

* [Vlad (Volodymyr) Pavlov](https://www.linkedin.com/in/vlpavlov/)
