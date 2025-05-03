""" Package with basic infrastructure for parameterizable classes.

This package provides the functionality for work with parameterizable classes:
classes that have (hyper) parameters which define object's configuration,
but not its internal contents or data. Such parameters are typically
passed to the .__init__() method.

The package provides an API for getting parameters' values from an object,
and for converting the parameters to and from a portable dictionary
(a dictionary that only contains basic types and portable sub-dictionaries).
"""



from typing import Any

CLASSNAME_PARAM_KEY = "__class__.__name__"
BUILTIN_TYPE_KEY = "__builtins__.__builtins__"

_known_parameterizable_classes = dict()
# Registry of parameterizable classes by name
# Used for object reconstruction from portable dictionaries


class ParameterizableClass:
    """ Base class for parameterizable classes.

    This class provides the basic functionality for parameterizable classes:
    classes that have (hyper) parameters which define object's configuration,
    and which are typically passed to the .__init__() method.
    The class provides an API for getting parameters' values from an object,
    and for converting the parameters to and from a portable dictionary
    (a dictionary that only contains basic types
    and portable sub-dictionaries).

    This class is not meant to be used directly, but to be subclassed
    by classes that need to be parameterizable.
    """
    def __init__(self):
        register_parameterizable_class(type(self))

    def __get_portable_params__(self) -> dict[str, Any]:
        """ Get the parameters of an object as a portable dictionary.

        These are the parameters that define the object's
        configuration (but not its internal contents or data)
        plus information about its type.

        They are returned as a 'portable' dictionary: a dictionary that only
        contains basic types and portable sub-dictionaries.
        """
        # Start with the object's parameters and add a class name for reconstruction
        portable_params = self.get_params()
        portable_params[CLASSNAME_PARAM_KEY] = self.__class__.__name__

        # Process each parameter based on its type:
        for key, value in portable_params.items():
            # Case 1: Parameter is itself a parameterizable object - recursively convert it
            if is_parameterizable(type(value)):
                portable_params[key] = value.__get_portable_params__()
            # Case 2: Parameter is a Python type object (like int, str) - store its name
            elif isinstance(value, type) and value in _supported_builtin_types:
                portable_params[key] = {
                    BUILTIN_TYPE_KEY: _supported_builtin_types[value]}
            # Case 3: Parameter is a basic type instance (like 5, "hello") - keep as is
            elif type(value) in _supported_builtin_types:
                continue
            # Case 4: Unsupported type - raise error
            else:
                raise ValueError(f"Unsupported type: {type(value)}")
        return portable_params

    @classmethod
    def __get_portable_default_params__(cls) -> dict[str, Any]:
        """ Get default parameters of a class as a portable dictionary.

        These are the values that are used to configure an object
        if no arguments are explicitly passed to the .__init__() method,
        plus information about the object's type.

        They are returned as a 'portable' dictionary: a dictionary that only
        contains basic types and portable sub-dictionaries.
        """
        params = cls().__get_portable_params__()
        return params

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
        """
        params = cls().get_params()
        return params


def get_object_from_portable_params(portable_params: dict[str, Any]) -> Any:
    """ Create an object from a dictionary of parameters.

    This function creates an object from a dictionary of portable parameters.
    The dictionary should have been created by the .__get_portable_params__()
    method of a ParameterizableClass object.
    """
    # Verify we have a dictionary with either class name or builtin type key
    assert isinstance(portable_params, dict)
    assert {CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY} & set(portable_params)

    # Special case: If this is a dictionary representing a builtin type (like int, str)
    if BUILTIN_TYPE_KEY in portable_params:
        assert len(portable_params) == 1  # Should only contain the type key
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
              set(value) & {CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY}):
            # This is a nested portable dictionary (either another parameterizable object
            # or a builtin type) - recursively convert it back to an object
            params[key] = get_object_from_portable_params(value)
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
    if not hasattr(cls, "__get_portable_params__"):
        return False
    if not callable(cls.__get_portable_params__):
        return False
    if not hasattr(cls, "__get_portable_default_params__"):
        return False
    if not callable(cls.__get_portable_default_params__):
        return False

    # All checks passed - this is a parameterizable class
    return True


def _smoketest_parameterizable_class(cls: Any):
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
    assert is_parameterizable(cls)
    default_params = cls.get_default_params()
    params = cls().get_params()
    assert isinstance(default_params, dict)
    assert isinstance(params, dict)
    assert default_params == params  # Default params should match params of a new instance
    return True


def _smoketest_known_parameterizable_classes():
    """ Run a smoketest on all known parameterizable classes.

    This function runs a basic unit test on all known parameterizable classes
    that have been registered with register_parameterizable_class().

    This is an internal testing function that can be used to validate the
    correctness of all registered parameterizable classes at once.
    """
    for class_name, cls in _known_parameterizable_classes.items():
        _smoketest_parameterizable_class(cls)


def register_parameterizable_class(new_parameterizable_class: Any):
    """ Register a parameterizable class.

    This function registers a parameterizable class so that it can be
    used with the get_object_from_portable_params()
    """
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