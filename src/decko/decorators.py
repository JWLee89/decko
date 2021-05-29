"""
Stateless version that provides only decorated functions
"""
import inspect
import typing as t
from functools import wraps, partial
from time import process_time
import threading

from .helper.validation import (
    raise_error_if_not_callable,
    raise_error_if_not_class_instance,
    is_instancemethod
)
from .helper.util import (
    create_instance,
    attach_property,
)
from .helper.exceptions import TooSlowError
from .immutable import ImmutableError


# -------------------------------------------
# ------------ Core decorators --------------
# -------------------------------------------


def decorator(*type_template_args) -> t.Any:
    """
    Decorate a function based on its type.
    Decorators come in two forms.
    :return:
    """
    print(f"type temp: {type_template_args}")

    def wrapper(newly_decorated_object: t.Union[t.Callable, t.Any]):
        """
        :param newly_decorated_object: The wrapped object from inner

        e.g. the inner_wrapped_object in the example below would be
        "decorated_function"

        @decorator
        def decorated_function(inputs):
            print(inputs)

        :param kw:
        """
        @wraps(newly_decorated_object)
        def returned_obj(*decorator_args, **decorator_kwargs):
            print(f"decorator_to_construct: {newly_decorated_object}, \n "
                  f"Decorated args: {decorator_args}, kwargs: {decorator_kwargs} \n"
                  f"returned object: {returned_obj}")

            def return_func(*args, **kwargs):
                print(f"args: {args}, kwargs: {kwargs}")
                return newly_decorated_object(*args, **kwargs)

            return return_func

        return returned_obj
    return wrapper


def optional_args(wrapped_func: t.Callable = None,
                  **kw) -> t.Callable:
    """
    Create function with optional arguments
    :param wrapped_func: The function to be wrapped
    :param callback: An
    :return:
    """
    if wrapped_func is None:
        return partial(optional_args, **kw)

    @wraps(wrapped_func)
    def returned_func(*args, **kwargs):
        output = returned_func(*args, **kwargs)
        return output

    return returned_func


# --------------------------------------------
# ------------ Utility decorators ------------
# --------------------------------------------


def stopwatch(callback: t = print):
    raise_error_if_not_callable(callback)

    def decorator(func: t.Callable) -> t.Callable:
        @wraps(func)
        def returned_func(*args, **kwargs):
            start_time = process_time()
            output = func(*args, **kwargs)
            time_elapsed = process_time() - start_time
            callback(time_elapsed)
            return output

        return returned_func

    return decorator


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

    def decorator(func: t.Callable) -> t.Callable:
        @wraps(func)
        def returned_func(*args, **kwargs):
            fire_event = predicate(*args, **kwargs)
            if fire_event:
                return func(*args, **kwargs)

        return returned_func

    return decorator


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

    def decorator(func):

        @wraps(func)
        def returned_func(*args, **kwargs):
            start = process_time() * 1000
            output = func(*args, **kwargs)
            elapsed = (process_time() * 1000) - start
            if elapsed > time_ms:
                callback(elapsed)
            return output

        return returned_func

    return decorator


def freeze(cls: t.Type[t.Any]) -> t.Type[t.Any]:
    """
    Completely freeze a class.
    A frozen class will raise an error if any of its properties
    are mutated or if new classes are added
    :param cls: A Class
    :return:
    :rtype:
    """
    raise_error_if_not_class_instance(cls)

    def do_freeze(slf, name, value):
        msg = f"Class {type(slf)} is frozen. " \
              f"Attempted to set attribute '{name}' to value: '{value}'"
        raise ImmutableError(msg)

    class Immutable(cls):
        """
        A basic immutable class
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            setattr(Immutable, '__setattr__', do_freeze)

    return Immutable


def singleton(thread_safe: bool = False) -> t.Type[t.Any]:
    """
    If decorated with singleton,
    this class will be a singleton object
    """

    def wrapper(wrapped_class: t.Any):
        raise_error_if_not_class_instance(wrapped_class)
        if thread_safe:
            class Singleton(type):
                __lock = threading.Lock()
                __instance = {}

                def __call__(cls, *args, **kwargs):
                    if cls not in cls.__instance:
                        with cls.__lock:
                            if cls not in cls.__instance:
                                cls.__instance[cls] = super(Singleton, cls).__call__(*args, **kwargs)
                    return cls.__instance[cls]
        else:
            class Singleton(type):
                __instance = {}

                def __call__(cls, *args, **kwargs):
                    if cls not in cls.__instance:
                        cls.__instance[cls] = super(Singleton, cls).__call__(*args, **kwargs)
                    return cls.__instance[cls]

        class SingletonWrapped(wrapped_class, metaclass=Singleton):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        return SingletonWrapped
    return wrapper


def instance_data(filter_predicate: t.Callable = None,
                  getter: t.Callable = None,
                  setter: t.Callable = None) -> t.Any:
    """
    Observe class instance variables and perform various actions when a class
    member variable is accessed or when a variable is overwritten with
    the "equals" operator.

    Note: This does not detect when items are being added to a t.List.
    If there is such a use case, try extending the t.List and overriding the
    core methods.

    :param filter_predicate: The items that we want to filter
    :param getter:
    :param setter:
    :return: The wrapped class with observable properties
    """

    if filter_predicate is None:
        filter_predicate = lambda x, y: True

    def wrapper(cls: t.Any, *arguments):

        raise_error_if_not_class_instance(cls)
        inst = create_instance(cls, *arguments)

        class ObservableClass(cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                # The new observable properties
                new_attrs = []

                # Create new attributes
                for prop, value in inst.__dict__.items():
                    if filter_predicate(prop, value):
                        temp = (f"_{cls.__name__}__{prop}", prop)
                        new_attrs.append(temp)

                # Update old attribute key with new prop key values
                for new_prop, old_prop in new_attrs:
                    setattr(self, new_prop, getattr(self, old_prop))
                    delattr(self, old_prop)

                # Create properties dynamically
                for prop, value in inst.__dict__.items():
                    # handle name mangling
                    attach_property(cls, prop, getter, setter)

        # Now, decorate each method with
        return ObservableClass

    return wrapper


def filter_by_output(predicate: t.Callable) -> t.Callable:
    """
    Return the value if it passes a predicate function.
    Else, return None.
    :param predicate: The predicate function. If output is True,
    return the actual output.
    """

    def decorator(func: t.Callable) -> t.Callable:
        @wraps(func)
        def returned_func(*args, **kwargs):
            output = func(*args, **kwargs)
            if predicate(output):
                return output

        return returned_func

    return decorator


def raise_error_if(condition: t.Callable) -> t.Callable:
    """
    Raise exception if a condition is met
    :param condition: A function that returns true when
    """

    def decorator(func: t.Callable) -> t.Callable:
        raise_error_if_not_callable(func)

        @wraps(func)
        def returned_func(*args, **kwargs):
            output = func(*args, **kwargs)
            trigger_condition = condition(output)
            if trigger_condition:
                raise RuntimeError(f"{raise_error_if.__name__}({condition.__name__}) "
                                   "triggered because condition was met.\n"
                                   f"Wrapped function: '{func.__name__}()' "
                                   f"yielded output value {output}")

        return returned_func

    return decorator


def truncate(limit: int) -> t.Callable:
    """
    Truncate a slice-able object
    :param limit: The maximum size of the target object
    """

    def decorator(func: t.Callable) -> t.Callable:

        raise_error_if_not_callable(func)

        @wraps(func)
        def decorated_func(*args, **kwargs):
            output: t.Union[str, t.List, t.Tuple] = func(*args, **kwargs)
            try:
                return output[:limit]
            except:
                raise TypeError(f"Cannot slice object: {output}")

        return decorated_func

    return decorator
