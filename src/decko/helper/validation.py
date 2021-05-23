import typing as t
import types
import inspect


def raise_error_if_not_callable(should_be_callable: t.Callable):
    if inspect.isclass(should_be_callable) \
            or not isinstance(should_be_callable, t.Callable):
        raise TypeError(f"Invalid type: {type(should_be_callable)}. "
                        "Please pass in a function. ")


def raise_error_if_not_class_instance(obj: t.Any):
    if not inspect.isclass(obj):
        raise TypeError("Target function decorates classes only. "
                        "Please pass in a class. "
                        f"Passed in type: {type(obj)}")


def is_class_instance(item) -> bool:
    """
    Check if item is a class instance.
    :param item: The item to evaluate
    """
    return inspect.isclass(item)


def is_iterable(obj) -> bool:
    iterable = True
    try:
        iter(obj)
    except TypeError:
        iterable = False
    return iterable


def check_instance_of(value: t.Any, target_type: t.Type):
    if not isinstance(value, target_type):
        raise TypeError(f"{value} must be of instance type {target_type}. "
                        f"{value} is of type: {type(value)}")


def isclassmethod(method):
    bound_to = getattr(method, '__self__', None)
    if not isinstance(bound_to, type):
        # must be bound to a class
        return False
    name = method.__name__
    for cls in bound_to.__mro__:
        descriptor = vars(cls).get(name)
        if descriptor is not None:
            return isinstance(descriptor, classmethod)
    return False


def is_method(func: t.Callable):
    """
    Returns true if is an instance of method. This method is designed to
    work in cases where no class context is provided.

    This does not include functions that are static methods or
    class methods
    :param func:
    :return:
    """
    # methods are callable, non-static and non-class method
    if not isinstance(func, t.Callable) or isinstance(func, types.FunctionType):
        return False

    properties = dir(func)
    if "__qualname__" in properties and '.' in func.__qualname__:
        return True
    elif "__func__" not in properties:
        return False
    return not isclassmethod(func)
