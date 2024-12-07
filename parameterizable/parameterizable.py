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


class ParameterizableClass:
    """ Base class for parameterizable classes.

    This class provides the basic functionality for parameterizable classes:
    classes that have (hyper) parameters which define object's configuration,
    and which are typically passed to the .__init__() method.
    The class provides an API for getting parameters' values from an object,
    and for converting the parameters to and from an portable dictionary
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
        portable_params = self.get_params()
        portable_params[CLASSNAME_PARAM_KEY] = self.__class__.__name__
        for key, value in portable_params.items():
            if is_parameterizable(type(value)):
                portable_params[key] = value.__get_portable_params__()
            elif isinstance(value, type) and value in _supported_builtin_types:
                portable_params[key] = {
                    BUILTIN_TYPE_KEY: _supported_builtin_types[value]}
            elif type(value) in _supported_builtin_types:
                continue
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
    assert isinstance(portable_params, dict)
    assert {CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY} & set(portable_params)

    if BUILTIN_TYPE_KEY in portable_params:
        assert len(portable_params) == 1
        type_name = portable_params[BUILTIN_TYPE_KEY]
        return _supported_builtin_type_names[type_name]

    params = dict()
    class_name = portable_params[CLASSNAME_PARAM_KEY]
    object_class = _known_parameterizable_classes[class_name]
    for key, value in portable_params.items():
        if key == CLASSNAME_PARAM_KEY:
            continue
        elif (isinstance(value, dict) and
              set(value) & {CLASSNAME_PARAM_KEY, BUILTIN_TYPE_KEY}):
            params[key] = get_object_from_portable_params(value)
        else:
            params[key] = value
    object = object_class(**params)
    return object

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
    if not isinstance(cls, type):
        return False
    if not hasattr(cls, "__get_portable_params__"):
        return False
    if not callable(cls.__get_portable_params__):
        return False
    if not hasattr(cls, "get_params"):
        return False
    if not callable(cls.get_params):
        return False
    if not hasattr(cls, "__get_portable_default_params__"):
        return False
    if not callable(cls.__get_portable_default_params__):
        return False
    if not hasattr(cls, "get_default_params"):
        return False
    if not callable(cls.get_default_params):
        return False
    return True


def _smoketest_parameterizable_class(cls: Any):
    """ Run a smoke test on a parameterizable class.

    This function runs a basic unit test on a parameterizable class.
    """
    assert is_parameterizable(cls)
    default_params = cls.get_default_params()
    params = cls().get_params()
    assert isinstance(default_params, dict)
    assert isinstance(params, dict)
    assert default_params == params
    return True


def _smoketest_known_parameterizable_classes():
    """ Run a smoketest on all known parameterizable classes.

    This function runs a basic unit test on all known parameterizable classes.
    """
    for class_name, cls in _known_parameterizable_classes.items():
        _smoketest_parameterizable_class(cls)


def register_parameterizable_class(obj: Any):
    """ Register a parameterizable class.

    This function registers a parameterizable class so that it can be
    used with the get_object_from_portable_params()
    """
    if (obj.__name__ in _known_parameterizable_classes
            and _known_parameterizable_classes[obj.__name__] == obj):
        return
    elif not is_parameterizable(obj):
        raise ValueError("Object is not parameterizable")

    _known_parameterizable_classes[obj.__name__] = obj

def is_registered(cls) -> bool:
    return cls.__name__ in _known_parameterizable_classes