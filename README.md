# parameterizable

Parameter manipulation for Python classes.

## What Is It?

`parameterizable` provides functionality for work with parameterizable 
classes: those that have (hyper) parameters which define object's configuration,
that is different from the object's internal contents or data.  Such parameters 
are typically passed to the `.__init__()` method when an object is created.

`parameterizable` allows to:
* Get parameters of an object as a dictionary.
* Get default parameters of a class as a dictionary.
* Serialize object's parameters to a 'portable' dictionary, that only 
contains basic (builtin) types and portable sub-dictionaries. 
* Recreate an object from its parameters, stored in a 'portable' dictionary.

## Usage
Inherit from `ParameterizableClass` class and define method `.get_params()`. 

## Key Classes, Functions, and Constants

* `ParameterizableClass` - a base class for parameterizable objects. 
You should derive your class from it if you want to 
use the functionality of this package.
* `ParameterizableClass.get_params()` - a method to be defined in a subclass,
returns the current parameters of an object as a dictionary.
* `ParameterizableClass.get_default_params()` - returns the default parameters
of the class as a dictionary.
* `ParameterizableClass.__get_portable_params__()` - returns a 'portable'
dictionary of the object's parameters.
* `ParameterizableClass.__get_portable_default_params__()` - returns 
a 'portable' dictionary of the class's default parameters.
* `is_parameterizable(obj)` - checks if an object or a class is parameterizable.
* `register_parameterizable_class(cls)` - registers a class as parameterizable.
This is required for `get_object_from_portable_dict()` to work 
with objects of the class.
* `get_object_from_portable_params()` - recreates an object from
a 'portable' dictionary. Only works for classes that were previously 
registered with `register_parameterizable_class()`.

## Short Example

Visit this Colab notebook for a short demonstration of the package usage:
[https://colab.research.google.com/drive/1myLzvM2g43_bLhEMazb4a4OZx8lsPrzd](https://colab.research.google.com/drive/1myLzvM2g43_bLhEMazb4a4OZx8lsPrzd)

## How To Get It?

The source code is hosted on GitHub at:
[https://github.com/pythagoras-dev/parameterizable](https://github.com/pythagoras-dev/parameterizable) 

Binary installers for the latest released version are available at the Python package index at:
[https://pypi.org/project/parameterizable](https://pypi.org/project/parameterizable)

        pip install parameterizable

## Dependencies

* [pytest](https://pytest.org)

## Key Contacts

* [Vlad (Volodymyr) Pavlov](https://www.linkedin.com/in/vlpavlov/)