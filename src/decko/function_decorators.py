"""
Stateless version that provides only decorated functions
"""
import typing as t
from functools import wraps
from time import process_time


def stopwatch(callback: t = print):
    if not isinstance(callback, t.Callable):
        raise TypeError("callback must be callable: "
                        f"passed in {callback} of type: {type(callback)}")

    def inner(func: t.Callable) -> t.Callable:

        @wraps(func)
        def returned_func(*args, **kwargs):
            start_time = process_time()
            output = func(*args, **kwargs)
            time_elapsed = process_time() - start_time
            callback(time_elapsed)
            return output
        return returned_func

    return inner
