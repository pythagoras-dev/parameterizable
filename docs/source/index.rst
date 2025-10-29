parameterizable
===============

.. image:: https://img.shields.io/pypi/v/parameterizable.svg
   :target: https://pypi.org/project/parameterizable/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/parameterizable.svg
   :target: https://pypi.org/project/parameterizable/
   :alt: Python versions

.. image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://github.com/pythagoras-dev/parameterizable/blob/master/LICENSE
   :alt: License: MIT

.. image:: https://img.shields.io/pypi/dm/parameterizable?color=blue
   :target: https://pypistats.org/packages/parameterizable
   :alt: Downloads

.. image:: https://app.readthedocs.org/projects/parameterizable/badge/?version=latest
   :target: https://parameterizable.readthedocs.io/en/latest/
   :alt: Documentation Status

.. image:: https://img.shields.io/badge/code_style-pep8-blue.svg
   :target: https://peps.python.org/pep-0008/
   :alt: Code style: pep8

.. image:: https://img.shields.io/badge/docstrings_style-Google-blue
   :target: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
   :alt: Docstring Style: Google


Parameter manipulation for Python classes.

What Is It?
-----------

``parameterizable`` provides functionality for work with parameterizable
classes: those that have (hyper)parameters which define an object's configuration,
that is different from the object's internal contents or data. Such parameters
are typically passed to the ``.__init__()`` method when an object is created.

``parameterizable`` allows you to:

* Get parameters of an object as a dictionary
* Get default parameters of a class as a dictionary
* Serialize an object's parameters to a JSON string
* Recreate the object from its parameters, stored in a JSON string

Why Is It Useful?
-----------------

``parameterizable`` is useful for developers working with
configurable Python objects, especially in scenarios involving
machine learning, scientific computing, or any domain where
an object's behavior is defined by its parameters. It provides:

* **Consistency**: Ensures a standardized way to handle parameters across different classes
* **Serialization**: Simplifies saving and loading configuration-defined objects using JSON
* **Reproducibility**: Facilitates recreating objects with the same configuration, which is critical for debugging and sharing experiments

By abstracting parameter handling, this library reduces boilerplate code
and improves maintainability.

Installation
------------

The source code is hosted on `GitHub <https://github.com/pythagoras-dev/parameterizable>`_.

Binary installers for the latest released version are available at the
`Python Package Index (PyPI) <https://pypi.org/project/parameterizable>`_.

Using **uv** (recommended):

.. code-block:: bash

   uv add parameterizable

Using **pip** (legacy alternative to uv):

.. code-block:: bash

   pip install parameterizable

Requirements
~~~~~~~~~~~~

* Python >= 3.10
* Runtime dependencies: none

For development:

* pytest (optional)

Quick Start
-----------

Here's a minimal example showing how to make your class parameterizable and serialize/deserialize it:

.. code-block:: python

   from parameterizable import ParameterizableClass, dumpjs, loadjs

   class MyModel(ParameterizableClass):
       def __init__(self, learning_rate=0.01, epochs=100):
           self.learning_rate = learning_rate
           self.epochs = epochs
           self.trained = False

       def get_params(self):
           return {
               'learning_rate': self.learning_rate,
               'epochs': self.epochs
           }

       @property
       def essential_param_names(self):
           return ['learning_rate', 'epochs']

   # Create an instance
   model = MyModel(learning_rate=0.001, epochs=50)

   # Serialize to JSON
   json_str = dumpjs(model)
   print(json_str)

   # Deserialize from JSON
   restored_model = loadjs(json_str)
   print(restored_model.learning_rate)  # 0.001
   print(restored_model.epochs)         # 50

Key Features
------------

Classes
~~~~~~~

* **ParameterizableClass**: Base class for parameterizable objects. Inherit from it to enable the library's features.
* **NotPicklableClass**: Mixin that prevents pickling/unpickling; inherit from it to make your class explicitly non-picklable.
* **JsonSerializedObject**: A string containing JSON-serialized object.

Methods and Properties
~~~~~~~~~~~~~~~~~~~~~~

* ``get_params()``: Implement in your subclass to return the configuration dictionary needed to recreate the object.
* ``get_default_params()``: Class method returning default parameters for the class as a dictionary.
* ``essential_param_names``: Implement in your subclass to return the names of the core parameters which determine the object's behavior.
* ``auxiliary_param_names``: Property that returns the names of the auxiliary parameters.
* ``get_jsparams()``: Serializes an object's parameters to a JSON string.
* ``get_essential_jsparams()``: Returns a JSON string with essential parameters only.
* ``get_auxiliary_jsparams()``: Returns a JSON string with auxiliary parameters only.
* ``get_default_jsparams()``: Class method returning default parameters for the class as a JSON string.

Functions
~~~~~~~~~

* ``dumpjs(obj)``: Serialize an object to a JSON string.
* ``loadjs(js)``: Deserialize an object from a JSON string.
* ``update_jsparams(js, updates)``: Update selected parameters in a JSON string without full deserialization.
* ``access_jsparams(js, names)``: Extract a subset of parameters from a JSON string.
* ``sort_dict_by_keys(d)``: Utility to produce a new dict whose keys are sorted alphabetically.

Usage Pattern
-------------

Most users will:

1. Inherit from ``ParameterizableClass`` in their own classes
2. Implement the ``.get_params()`` method to expose the configuration needed to recreate the object
3. (Optional) Implement the ``.essential_param_names`` property to expose the core parameters which determine the object's behavior

If ``essential_param_names`` is not implemented, all parameters are considered essential.

API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: API Documentation:

   api/modules

Contributing
------------

Contributions are welcome! Please see the `contributing guide <https://github.com/pythagoras-dev/parameterizable/blob/master/contributing.md>`_
for details on:

* Setting up the development environment
* Running tests
* Code style guidelines
* Commit message conventions
* Submitting pull requests

License
-------

``parameterizable`` is licensed under the MIT License.
See the `LICENSE <https://github.com/pythagoras-dev/parameterizable/blob/master/LICENSE>`_ file for details.

Resources
---------

* **GitHub**: https://github.com/pythagoras-dev/parameterizable
* **PyPI**: https://pypi.org/project/parameterizable/
* **Documentation**: https://parameterizable.readthedocs.io/

Contact
-------

* **Maintainer**: `Vlad (Volodymyr) Pavlov <https://www.linkedin.com/in/vlpavlov/>`_
* **Email**: vlpavlov@ieee.org

Indices and Tables
==================

* :ref:`genindex`
* :ref:`search`