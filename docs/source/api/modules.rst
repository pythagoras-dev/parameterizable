API Reference
=============

Complete API documentation for all modules, classes, and functions in mixinforge.

Core Components
---------------

Mixins and Metaclasses
~~~~~~~~~~~~~~~~~~~~~~

The library provides several mixins and metaclasses for common design patterns:

* **ParameterizableMixin** - Parameter management and JSON serialization
* **ImmutableParameterizableMixin** - Immutable objects with params-based identity
* **CacheablePropertiesMixin** - Automatic cached property management
* **NotPicklableMixin** - Prevent object pickling
* **SingleThreadEnforcerMixin** - Thread safety enforcement
* **SingletonMixin** - Singleton pattern implementation
* **GuardedInitMeta** - Initialization lifecycle control

Utility Functions
~~~~~~~~~~~~~~~~~

Helper functions for common operations:

* **JSON processing** - dumpjs, loadjs, update_jsparams, access_jsparams
* **Dictionary utilities** - sort_dict_by_keys
* **Collection processing** - nested structure handling

Command Line Tools
~~~~~~~~~~~~~~~~~~

Project analysis and maintenance utilities:

* **mf-get-stats** - Generate project metrics
* **mf-clear-cache** - Remove Python cache files

Full Module Documentation
--------------------------

.. toctree::
   :maxdepth: 4

   mixinforge
