import typing as t
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


def is_classmethod(method: t.Callable):
    """
    A python method is a wrapper around a function that also
    holds a reference to the class it is a method of.
    When bound, it also holds a reference to the instance.

    @see https://stackoverflow.com/questions/12935241/python-call-instance-method-using-func
    :param method:

    """
    #     print(instance.a_method)    # Bounded
    #     print(AClass.a_method)      # Unbounded
    bound_to: t.Type = getattr(method, '__self__', None)
    # Bound to: <class '__main__.AClass'>, False
    # If double decorated with staticmethod and classmethod
    # Bound to: <__main__.AClass object at 0x7ffb18699fd0>, True
    if not isinstance(bound_to, type):
        # must be bound to a class
        return False
    name: str = method.__name__
    # MRO = Method resolution order
    # E.g. Class A: pass
    # A.__mro__
    # Output: (<class '__main__.AClass'>, <class 'object'>)
    for cls in bound_to.__mro__:
        # Get decorator
        descriptor = vars(cls).get(name)
        if descriptor is not None:
            return isinstance(descriptor, classmethod)
    return False


def is_staticmethod(method: t.Callable):
    bound_to: t.Type = getattr(method, '__self__', None)
    # Static methods are unbound
    return not bound_to and isinstance(method, staticmethod)


def is_instancemethod(func: t.Callable) -> bool:
    """
    Returns true if is an instance of method. This method is designed to
    work in cases where no class context is provided.

    This does not include functions that are static methods or
    class methods
    :param func:
    :return:
    """
    # methods are callable
    if not isinstance(func, t.Callable):
        return False

    return not is_classmethod(func) and not is_staticmethod(func) \
           and getattr(func, '__self__', None) is not None
