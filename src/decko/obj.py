"""
Creates decorators that are used to create objects
"""
import typing as t
# Local imports
from .decorators import deckorator


@deckorator(t.Callable)
def generator(decorated_function: t.Callable,
              preprocessor_func: t.Callable,
              *args, **kwargs):

    output = decorated_function(*args, **kwargs)
    return output

