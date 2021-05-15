from functools import wraps
from typing import Callable

# from .helper.validation import (
#     raise_error_if_not_callable,
# )


def decorate_func_without_args(func: Callable):

    # raise_error_if_not_callable(func)

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
