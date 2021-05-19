"""
Stateless version that provides only decorated functions
"""
import typing as t
from functools import wraps
from time import process_time
from .helper.validation import raise_error_if_not_callable
from .helper.exceptions import TooSlowError


def stopwatch(callback: t = print):
    raise_error_if_not_callable(callback)

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


def execute_if(predicate: t.Callable) -> t.Callable:
    """
    Given a t.List of subscribed callables and an predicate function,
    create a wrapper that fires events when predicates are fulfilled

    >> Code sample
    ----------------------------------

    def do_something(output, instance, arr):
        print(f"Output: {output}. Triggered by array: {arr}")


    # The decorated function will fire if the predicate function
    # outputs a truthy value.

    @execute_if(lambda x, arr: len(arr) > 5)
    def do_something(arr):
        return sum(arr)

    if __name__ == "__main__":
        # This should fire an event since we called
        test = do_something([1, 2, 3, 4, 5, 6])
        print(do_something([20, 30]))

    >> End code sample
    ----------------------------------
    :param predicate: The condition for triggering the event
    :return: The wrapped function
    """

    def inner(func: t.Callable) -> t.Callable:
        @wraps(func)
        def returned_func(*args, **kwargs):
            fire_event = predicate(*args, **kwargs)
            if fire_event:
                return func(*args, **kwargs)
        return returned_func
    return inner


def slower_than(time_ms: float, callback: t.Callable = None):
    """
    Executes callback if time taken takes longer than specified time
    :param time_ms: If the function does not complete in specified time,
    :param callback: The function that is called if decorator is triggered
    a warning will be raised.
    :return:
    """
    if callback is None:
        def callback(time_elapsed):
            raise TooSlowError("Function took too long to run ... "
                               f"Should take less than {time_ms} "
                               f"ms but took {time_elapsed} ms")

    raise_error_if_not_callable(callback)

    def inner(func):

        @wraps(func)
        def returned_func(*args, **kwargs):
            start = process_time() * 1000
            output = func(*args, **kwargs)
            elapsed = (process_time() * 1000) - start
            if elapsed > time_ms:
                callback(elapsed)
            return output

        return returned_func
    return inner
