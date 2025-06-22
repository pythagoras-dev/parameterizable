""" Package with basic infrastructure for parameterizable classes.

This package provides the functionality for work with parameterizable classes:
classes that have (hyper) parameters which define an object's configuration,
but not its internal contents or data. Such parameters are typically
passed to the .__init__() method.

The package provides an API for getting parameters' values from an object,
and for converting the parameters to and from a portable dictionary
(a dictionary with sorted str keys that only contains
basic types and portable sub-dictionaries).
"""


from typing import Any

from .dict_sorter import sort_dict_by_keys

CLASSNAME_PARAM_KEY = "__class__.__name__"
BUILTIN_TYPE_KEY = "__builtins__.__builtins__"

_known_parameterizable_classes = dict()
# Registry of parameterizable classes by name
# Used for object reconstruction from portable dictionaries


class ParameterizableClass:
    """ Base class for parameterizable classes.

    This class provides the basic functionality for parameterizable classes:
    classes that have (hyper) parameters which define an object's configuration
    and which are typically passed to the .__init__() method.
    The class provides an API for getting parameters' values from an object
    and for converting the parameters to and from a portable dictionary
    (a dictionary that only contains basic types
    and portable sub-dictionaries).

    This class is not meant to be used directly but to be subclassed
    by classes that need to be parameterizable.
    """
    def __init__(self):
        register_parameterizable_class(type(self))

    def get_portable_params(self) -> dict[str, Any]:
        """ Get the parameters of an object as a portable dictionary.

        These are the parameters that define the object's
        configuration (but not its internal contents or data)
        plus information about its type.

        They are returned as a 'portable' dictionary:
        a dictionary with sorted str keys that only contain basic types
        and portable sub-dictionaries as values.
        """
        # Start with the object's parameters and add a class name for reconstruction
        portable_params = self.get_params()
        portable_params[CLASSNAME_PARAM_KEY] = self.__class__.__name__

        # Process each parameter based on its type:
        for key, value in portable_params.items():
            # Case 1: Parameter is itself a parameterizable object - recursively convert it
            if is_parameterizable(type(value)):
                portable_params[key] = value.get_portable_params()
            # Case 2: Parameter is a Python type object (like int, str) - store its name
            elif isinstance(value, type) and value in _supported_builtin_types:
                portable_params[key] = {
                    BUILTIN_TYPE_KEY: _supported_builtin_types[value]}
            # Case 3: Parameter is a collection (list ot dict, tuples are not supported) -
            # process its elements
            elif isinstance(value, list):
                portable_params[key] = [
                    item.get_portable_params() if is_parameterizable(type(item))
                    else item
                    for item in value
                ]
            elif isinstance(value, dict):
                portable_params[key] = {
                    k: v.get_portable_params() if is_parameterizable(type(v)) else v
                    for k, v in value.items()
                }
            # Case 4: Parameter is a basic type instance (like 5, "hello") - keep as is
            elif type(value) in _supported_builtin_types:
                continue
            # Case 5: Unsupported type - raise error
            else:
                raise ValueError(f"Unsupported type: {type(value)}")

        sorted_portable_params = sort_dict_by_keys(portable_params)
        return sorted_portable_params

    @classmethod
    def get_portable_default_params(cls) -> dict[str, Any]:
        """ Get default parameters of a class as a portable dictionary.

        These are the values that are used to configure an object
        if no arguments are explicitly passed to the .__init__() method,
        plus information about the object's type.

        They are returned as a 'portable' dictionary: a dictionary that only
        contains basic types and portable sub-dictionaries.
        """
        # Get default parameters and convert to portable dictionary
        default_params = cls.get_default_params()

        # Create a portable dictionary with class name
        portable_params = default_params.copy()
        portable_params[CLASSNAME_PARAM_KEY] = cls.__name__

        # Process each parameter based on its type (similar to get_portable_params)
        for key, value in list(portable_params.items()):
            # Case 1: Parameter is itself a parameterizable object - recursively convert it
            if is_parameterizable(type(value)):
                portable_params[key] = value.get_portable_params()
            # Case 2: Parameter is a Python type object (like int, str) - store its name
            elif isinstance(value, type) and value in _supported_builtin_types:
                portable_params[key] = {
                    BUILTIN_TYPE_KEY: _supported_builtin_types[value]}
            # Case 3: Parameter is a collection (list, dict, etc.) - process its elements
            elif isinstance(value, (list, tuple)):
                portable_params[key] = [
                    item.get_portable_params() if is_parameterizable(type(item))
                    else item
                    for item in value
                ]
            elif isinstance(value, dict):
                portable_params[key] = {
                    k: v.get_portable_params() if is_parameterizable(type(v)) else v
                    for k, v in value.items()
                }
            # Case 4: Parameter is a basic type instance (like 5, "hello") - keep as is
            elif type(value) in _supported_builtin_types:
                continue
            # Case 5: Unsupported type - raise error
            else:
                raise ValueError(f"Unsupported type: {type(value)}")

        sorted_portable_params = sort_dict_by_keys(portable_params)
        return sorted_portable_params

    def get_params(self) -> dict[str, Any]:
        """ Get the parameters of the object as a dictionary.

        This method must be implemented by subclasses.

        These parameters define the object's configuration,
        but not its internal contents or data. They are typically passed
        to the .__init__() method of the object at the time of its creation.
        """
        params = dict()
        return params

    @classmethod
    def get_default_params(cls) -> dict[str, Any]:
        """ Get the default parameters of the class as a dictionary.

        Default parameters are the values that are used to
        configure an object if no arguments are explicitly passed to
        the .__init__() method.

        This is a safe fallback implementation that creates an instance of
        the class to get default parameters. Subclasses can override this method
        to provide default parameters without creating an instance, which is
        recommended if the __init__ method has side effects.
        """
        params = cls().get_params()
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


def get_object_from_portable_params(portable_params: dict[str, Any]) -> Any:
    """ Create an object from a dictionary of parameters.

    This function creates an object from a dictionary of portable parameters.
    The dictionary should have been created by the .get_portable_params()
    method of a ParameterizableClass object.
    """
    # Verify we have a dictionary with either class name or builtin type key
    if not isinstance(portable_params, dict):
        raise TypeError("portable_params must be a dictionary")
    if not {CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY} & set(portable_params):
        raise ValueError(f"portable_params must contain either"
                         f" {CLASSNAME_PARAM_KEY} or {BUILTIN_TYPE_KEY}")
    if not list(portable_params.keys()) == sorted(portable_params.keys()):
        raise ValueError("portable_params must be a dictionary with sorted keys")

    # Special case: If this is a dictionary representing a builtin type (like int, str)
    if BUILTIN_TYPE_KEY in portable_params:
        if len(portable_params) != 1:
            raise ValueError(f"Dictionary with {BUILTIN_TYPE_KEY} "
                             "should only contain the type key")
        type_name = portable_params[BUILTIN_TYPE_KEY]
        return _supported_builtin_type_names[type_name]  # Return the actual type object

    # Regular case: Create an object from its parameters
    params = dict()
    class_name = portable_params[CLASSNAME_PARAM_KEY]
    # Look up the class in our registry
    object_class = _known_parameterizable_classes[class_name]

    # Process each parameter
    for key, value in portable_params.items():
        if key == CLASSNAME_PARAM_KEY:
            # Skip the class name key as it's not a parameter for __init__
            continue
        elif (isinstance(value, dict) and
              {CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY} & set(value)):
            # This is a nested portable dictionary (either another parameterizable object
            # or a builtin type) - recursively convert it back to an object
            params[key] = get_object_from_portable_params(value)
        elif isinstance(value, list):
            # This is a list - process its elements recursively
            params[key] = [
                get_object_from_portable_params(item) 
                if isinstance(item, dict) and 
                   ({CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY} & set(item))
                else item
                for item in value
            ]
        elif isinstance(value, dict):
            # This is a dictionary - process its values recursively
            params[key] = {
                k: get_object_from_portable_params(v) 
                if isinstance(v, dict) and 
                   ({CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY} & set(v))
                else v
                for k, v in value.items()
            }
        else:
            # This is a basic type value - use it directly
            params[key] = value
    object = object_class(**params)
    return object

# Dictionary mapping Python built-in types to their string representations
# Used when serializing type objects to portable dictionaries
_supported_builtin_types = {
    int:"__builtins__.int"
    ,float:"__builtins__.float"
    ,str:"__builtins__.str"
    ,bool:"__builtins__.bool"
    ,complex:"__builtins__.complex"
    ,list:"__builtins__.list"
    ,tuple:"__builtins__.tuple"
    ,dict:"__builtins__.dict"
    ,set:"__builtins__.set"
    ,frozenset:"__builtins__.frozenset"
    ,type:"__builtins__.type"
    ,type(None):"__builtins__.NoneType"
    }

# Reverse mapping of _supported_builtin_types
# Maps string representations back to their corresponding Python types
# Used when deserializing type objects from portable dictionaries
_supported_builtin_type_names = {
    name:supported_type for supported_type, name
    in _supported_builtin_types.items()}



def is_parameterizable(cls: Any) -> bool:
    """ Check if a class is parameterizable.

    This function checks if a class is parameterizable, i.e. if it has
    the necessary methods to get and set parameters.

    The easiest way to make a class parameterizable is to subclass
    the ParameterizableClass class.
    """
    # First, check if we're dealing with a class (type) and not an instance
    if not isinstance(cls, type):
        return False

    if issubclass(cls, ParameterizableClass):
        return True

    # Check for all required methods that make a class parameterizable
    # These checks ensure the class has the complete interface needed for
    # parameter handling, serialization, and deserialization

    # Methods for parameter access
    if not hasattr(cls, "get_params"):
        return False
    if not callable(cls.get_params):
        return False
    if not hasattr(cls, "get_default_params"):
        return False
    if not callable(cls.get_default_params):
        return False

    # Methods for portable dictionary conversion
    if not hasattr(cls, "get_portable_params"):
        return False
    if not callable(cls.get_portable_params):
        return False
    if not hasattr(cls, "get_portable_default_params"):
        return False
    if not callable(cls.get_portable_default_params):
        return False

    # All checks passed - this is a parameterizable class
    return True


def smoketest_parameterizable_class(cls: Any):
    """ Run a smoke test on a parameterizable class.

    This function runs a basic unit test on a parameterizable class to verify
    that it correctly implements the parameterizable interface. It checks:
    1. That the class is recognized as parameterizable
    2. That get_default_params() returns a dictionary
    3. That an instance's get_params() returns a dictionary
    4. That default parameters match the parameters of a newly created instance

    This is an internal testing function used to validate the correctness
    of parameterizable class implementations.
    """
    if not is_parameterizable(cls):
        raise TypeError(f"Class {cls.__name__} is not parameterizable")
    default_params = cls.get_default_params()
    params = cls().get_params()
    if not isinstance(default_params, dict):
        raise TypeError(f"get_default_params() must return a dictionary,"
                        " got {type(default_params)} instead")
    if not isinstance(params, dict):
        raise TypeError(f"get_params() must return a dictionary,"
                        " got {type(params)} instead")
    for key in default_params:
        if not isinstance(key, str):
            raise TypeError(f"Default parameters keys must be strings,"
                            f" got {type(key)} instead")
    for key in params:
        if not isinstance(key, str):
            raise TypeError(f"Parameters keys must be strings,"
                            f" got {type(key)} instead")
    if list(default_params.keys()) != sorted(default_params.keys()):
        raise ValueError("Default parameters dictionary is not sorted by keys")
    if list(params.keys()) != sorted(params.keys()):
        raise ValueError("Parameters dictionary is not sorted by keys")
    if default_params != params:
        raise ValueError("Default parameters do not match "
                         "parameters of a new instance")

    if not is_registered(cls):
        raise ValueError(f"Class {cls.__name__} is not registered. "
                         "Please register it with register_parameterizable_class().")

    default_portable_params = cls.get_portable_default_params()
    portable_params = cls().get_portable_params()
    restored_from_defaults = get_object_from_portable_params(default_portable_params)
    restored_from_params = get_object_from_portable_params(portable_params)
    if not restored_from_defaults.get_params() == default_params:
        raise ValueError(f"Smoke test for parameterizable class {cls.__name__} "
                         "has failed")
    if not restored_from_params.get_params() == params:
        raise ValueError(f"Smoke test for parameterizable class {cls.__name__} "
                         "has failed")

    return True


def smoketest_all_known_parameterizable_classes():
    """ Run a smoketest on all known parameterizable classes.

    This function runs a basic unit test on all known parameterizable classes
    that have been registered with register_parameterizable_class().

    This is an internal testing function that can be used to validate the
    correctness of all registered parameterizable classes at once.
    """
    for class_name, cls in _known_parameterizable_classes.items():
        smoketest_parameterizable_class(cls)


def register_parameterizable_class(new_parameterizable_class: Any):
    """ Register a parameterizable class.

    This function registers a parameterizable class so that it can be
    used with the get_object_from_portable_params()
    """
    if not isinstance(new_parameterizable_class, type):
        raise TypeError("new_parameterizable_class must be a class type"
                        f", got {type(new_parameterizable_class)} instead")

    # If the class is already registered with the same name and identity,
    # there's nothing to do - avoid duplicate registrations
    # otherwise, raise an error
    if new_parameterizable_class.__name__ in _known_parameterizable_classes:
        if _known_parameterizable_classes[new_parameterizable_class.__name__
            ] == new_parameterizable_class:
            return
        else:
            raise ValueError(
                f"Class {new_parameterizable_class.__name__} is already registered "
                "with a different identity. Please use a different name or "
                "unregister the existing class first.")

    # Verify that the object is actually parameterizable before registering
    elif not is_parameterizable(new_parameterizable_class):
        raise ValueError(f"Class {new_parameterizable_class.__name__} "
                         "is not parameterizable hence cannot be registered.")

    # Add the class to the registry using its name as the key
    _known_parameterizable_classes[new_parameterizable_class.__name__
        ] = new_parameterizable_class


def is_registered(cls) -> bool:
    """ Check if a class is registered in the parameterizable registry.

    This is a helper function to verify if a class has been registered with
    register_parameterizable_class(). Only registered classes can be recreated
    from portable dictionaries using get_object_from_portable_params().

    Args:
        cls: The class to check

    Returns:
        bool: True if the class is registered, False otherwise
    """
    return cls.__name__ in _known_parameterizable_classes