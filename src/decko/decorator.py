from functools import wraps
from typing import Any, Callable

from helper import util


def raise_error_if_not_callable(should_be_callable: Callable):
    if util.is_class_instance(should_be_callable) \
            or not isinstance(should_be_callable, Callable):
        raise TypeError(f"Invalid type: {type(should_be_callable)}. "
                        "Please pass in a function. ")


def raise_error_if_not_class_instance(obj: Any):
    if not util.is_class_instance(obj):
        raise TypeError("Target function decorates classes only. "
                        "Please pass in a class. "
                        f"Passed in type: {type(obj)}")


def decorate_func_without_args(func: Callable):

    raise_error_if_not_callable(func)

    @wraps(func)
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    return inner


def decorate_func(*a, **kw):
    def inner(func: Callable):
        return decorate_func_without_args(func)
    return inner


@decorate_func_without_args
def do_something(name):
    print(f"hi, my name is: {name}")


if __name__ == "__main__":
    do_something("teemo")
