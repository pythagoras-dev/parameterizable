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
Inherit from `ParameterizableClass` class and/or define method `.get_params()`
in your class.

## Key Classes, Functions, and Constants

* `ParameterizableClass` - a base class for parameterizable objects. 
You should derive your class from it if you want to 
use the functionality of this package.
* `ParameterizableClass.get_params()` - a method to be defined in a subclass,
returns the current parameters of an object as a regular dictionary.
* `ParameterizableClass.get_default_params()` - returns the default parameters
of the class as a regular dictionary.
* `dumps()` - serializes an object's parameters into a JSON string representation.
* `loads()` - deserializes a JSON string back into an object with the stored parameters.

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

## Dependencies

* [pytest](https://pytest.org)

## Key Contacts

* [Vlad (Volodymyr) Pavlov](https://www.linkedin.com/in/vlpavlov/)
