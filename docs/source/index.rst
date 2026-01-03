mixinforge
==========

.. image:: https://img.shields.io/pypi/v/mixinforge.svg
   :target: https://pypi.org/project/mixinforge/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/mixinforge.svg
   :target: https://pypi.org/project/mixinforge/
   :alt: Python versions

.. image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://github.com/pythagoras-dev/mixinforge/blob/master/LICENSE
   :alt: License: MIT

.. image:: https://img.shields.io/pypi/dm/mixinforge?color=blue
   :target: https://pypistats.org/packages/mixinforge
   :alt: Downloads

.. image:: https://app.readthedocs.org/projects/mixinforge/badge/?version=latest
   :target: https://mixinforge.readthedocs.io/en/latest/
   :alt: Documentation Status

.. image:: https://img.shields.io/badge/code_style-pep8-blue.svg
   :target: https://peps.python.org/pep-0008/
   :alt: Code style: pep8

.. image:: https://img.shields.io/badge/docstrings_style-Google-blue
   :target: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
   :alt: Docstring Style: Google

A collection of Python mixins and utilities for building robust, configurable classes.

What Is It?
-----------

``mixinforge`` is a lightweight library providing reusable mixins and utility
functions that help you build well-structured Python classes. It offers tools for:

* **Parameter management** — Track, serialize, and deserialize class configuration parameters
* **Cache management** — Automatically discover and invalidate ``cached_property`` attributes
* **Initialization control** — Enforce strict initialization contracts with lifecycle hooks
* **Thread safety** — Enforce single-threaded execution with multi-process support
* **Singleton pattern** — Ensure each subclass maintains exactly one instance
* **Pickle prevention** — Explicitly prevent objects from being pickled when serialization is unsafe
* **JSON serialization** — Convert objects and parameters to/from portable JSON representations
* **Dictionary utilities** — Helper functions for consistent dictionary handling

Quick Example
-------------

Here's a quick example demonstrating parameter management and JSON serialization:

.. code-block:: python

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

Installation
------------

The source code is hosted on `GitHub <https://github.com/pythagoras-dev/mixinforge>`_.

Binary installers for the latest released version are available at the
`Python Package Index (PyPI) <https://pypi.org/project/mixinforge>`_.

Using **uv** (recommended):

.. code-block:: bash

   uv add mixinforge

Using **pip**:

.. code-block:: bash

   pip install mixinforge

Requirements
~~~~~~~~~~~~

* Python >= 3.11
* Runtime dependencies: none

For development:

* pytest (optional)

Available Mixins and Metaclasses
--------------------------------

ParameterizableMixin
~~~~~~~~~~~~~~~~~~~~

A base class for objects with configuration parameters. Enables standardized
parameter access, JSON serialization, and distinguishes between essential and
auxiliary parameters.

.. code-block:: python

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

CacheablePropertiesMixin
~~~~~~~~~~~~~~~~~~~~~~~~

A mixin for managing ``functools.cached_property`` attributes with automatic
discovery and invalidation across the class hierarchy.

.. code-block:: python

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

NotPicklableMixin
~~~~~~~~~~~~~~~~~

A mixin that explicitly prevents objects from being pickled or unpickled.
Useful for objects that hold non-serializable resources like database connections,
file handles, or network sockets.

.. code-block:: python

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

GuardedInitMeta
~~~~~~~~~~~~~~~

A metaclass that enforces strict initialization control and provides lifecycle
hooks. It ensures that ``_init_finished`` is ``False`` during ``__init__`` and
automatically sets it to ``True`` afterward, enabling reliable initialization
state checks.

.. code-block:: python

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

SingleThreadEnforcerMixin
~~~~~~~~~~~~~~~~~~~~~~~~~

A mixin to enforce single-threaded execution with multi-process support.
Ensures methods are called only from the thread that first instantiated the
object, while automatically supporting process-based parallelism through fork
detection.

.. code-block:: python

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

SingletonMixin
~~~~~~~~~~~~~~

A mixin for implementing the singleton pattern. Ensures each subclass maintains
exactly one instance that is returned on every instantiation attempt. Useful for
classes that should have only a single instance throughout the application
lifetime, such as configuration managers or resource coordinators.

.. code-block:: python

   from mixinforge import SingletonMixin


   class ConfigManager(SingletonMixin):
       def __init__(self):
           if not hasattr(self, 'initialized'):
               self.config = {}
               self.initialized = True

       def get_params(self) -> dict:
           return self.config


   # Both variables reference the same instance
   config1 = ConfigManager()
   config2 = ConfigManager()
   assert config1 is config2  # True

   # Modifications affect all references
   config1.config['key'] = 'value'
   assert config2.config['key'] == 'value'  # True

CLI Commands
------------

mixinforge provides command-line tools for project analysis and maintenance.

mf-stats
~~~~~~~~

Generate project metrics and save to file:

.. code-block:: bash

   # Analyze current directory
   mf-stats

   # Analyze specific directory
   mf-stats /path/to/project

   # Specify custom output filename
   mf-stats --output my_metrics.md

Generates a markdown report with code statistics including lines of code (LOC),
source lines of code (SLOC), class counts, function counts, and file counts,
broken down by main code and unit tests.

mf-clean-cache
~~~~~~~~~~~~~~

Remove Python cache files from a directory and its subdirectories:

.. code-block:: bash

   # Clean current directory
   mf-clean-cache

   # Clean specific directory
   mf-clean-cache /path/to/project

   # Specify custom report filename
   mf-clean-cache --output cleanup_report.md

Removes ``__pycache__`` directories, ``.pyc`` files, ``.pyo`` files, and cache
directories from pytest, mypy, ruff, hypothesis, tox, and coverage tools.
Generates a detailed markdown report of removed items.

Utility Functions
-----------------

JSON Serialization
~~~~~~~~~~~~~~~~~~

.. code-block:: python

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

Dictionary Sorting
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from mixinforge import sort_dict_by_keys

   # Sort dictionary keys alphabetically
   sorted_dict = sort_dict_by_keys({"zebra": 1, "apple": 2, "mango": 3})
   # {"apple": 2, "mango": 3, "zebra": 1}

API Reference
-------------

Mixins
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Mixin
     - Description
   * - ``ParameterizableMixin``
     - Base class for parameterizable objects with JSON serialization support
   * - ``CacheablePropertiesMixin``
     - Automatic discovery and invalidation of ``cached_property`` attributes
   * - ``NotPicklableMixin``
     - Prevents pickling/unpickling of objects
   * - ``SingleThreadEnforcerMixin``
     - Enforces single-threaded execution with multi-process support
   * - ``SingletonMixin``
     - Ensures each subclass maintains exactly one instance

Metaclasses
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Metaclass
     - Description
   * - ``GuardedInitMeta``
     - Metaclass for strict initialization control and lifecycle hooks (``__post_init__``, ``__post_setstate__``)

Functions
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Function
     - Description
   * - ``dumpjs(obj)``
     - Serialize an object to a JSON string
   * - ``loadjs(js)``
     - Deserialize a JSON string back to an object
   * - ``update_jsparams(js, **updates)``
     - Update parameters in a JSON string without full deserialization
   * - ``access_jsparams(js, *names)``
     - Extract specific parameters from a JSON string
   * - ``sort_dict_by_keys(d)``
     - Return a new dictionary with keys sorted alphabetically

Types
~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Type
     - Description
   * - ``JsonSerializedObject``
     - Type alias for JSON strings produced by ``dumpjs``

Full API Documentation
----------------------

.. toctree::
   :maxdepth: 2
   :caption: API Documentation:

   api/modules

Contributing
------------

Contributions are welcome! Please see the `contributing guide <https://github.com/pythagoras-dev/mixinforge/blob/master/CONTRIBUTING.md>`_
for details on:

* Setting up the development environment
* Running tests
* Code style guidelines
* Commit message conventions
* Submitting pull requests

License
-------

``mixinforge`` is licensed under the MIT License.
See the `LICENSE <https://github.com/pythagoras-dev/mixinforge/blob/master/LICENSE>`_ file for details.

Resources
---------

* **GitHub**: https://github.com/pythagoras-dev/mixinforge
* **PyPI**: https://pypi.org/project/mixinforge/
* **Documentation**: https://mixinforge.readthedocs.io/

Contact
-------

* **Maintainer**: `Vlad (Volodymyr) Pavlov <https://www.linkedin.com/in/vlpavlov/>`_
* **Email**: vlpavlov@ieee.org

Indices and Tables
==================

* :ref:`genindex`
* :ref:`search`
