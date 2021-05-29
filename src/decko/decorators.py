"""
Stateless version that provides only decorated functions.
This API will be consumed by users who want access
to decorator functions.
The bells and whistles such as state management
and debugging / profiling utilities will be provided
by each Decko instance.
"""
import typing as t
from functools import wraps, partial
from time import process_time
import threading

from .helper.validation import (
    raise_error_if_not_callable,
    raise_error_if_not_class_instance,
)
from .helper.util import (
    create_instance,
    attach_property,
)
from .helper.exceptions import TooSlowError
from .immutable import ImmutableError
from types import MappingProxyType

__DECORATOR_SPECS__ = MappingProxyType({
    # By default, a type check is performed on decorators
    # to ensure that the defined functions meet specifications
    'enable_type_check': (bool, True)
})


def _set_defaults_if_not_defined(user_specs: t.Dict,
                                 default_specs: t.Mapping) -> None:
    """
    Update user_specs with default values if not specified.
    Also does a type check on user specifications to ensure
    that type validity and sanity is maintained.
    This modifies the original

    :param user_specs: The specifications provided by the user
    :param default_specs: A dictionary of default specifications
    """
    for prop_name, (prop_type, default_value) in default_specs.items():
        # Set default values if not defined by user
        if prop_name not in user_specs:
            user_specs[prop_name] = default_value
            continue

        # Value exists at this point
        user_value: t.Any = user_specs[prop_name]

        # If the value passed by the user does not meet
        # specifications, raise an error
        if not isinstance(user_value, prop_type):
            raise TypeError(f"property: '{prop_name}' should be of type: {prop_type}. "
                            f"Passed in value: '{user_value}' "
                            f"of type: '{type(user_value)}'")


# -------------------------------------------
# ------------ Core decorators --------------
# -------------------------------------------


def decorator(*type_template_args, **kw) -> t.Any:
    """
    Decorate a function based on its type.
    Decorators come in two forms:
        - Function decorators
        - Class decorators
    """
    _set_defaults_if_not_defined(kw, __DECORATOR_SPECS__)
    print(f"type temp: {type_template_args}, specs: {kw}")

    # TODO: After finishing function api, work on class api.
    def wrapper(newly_decorated_object: t.Union[t.Callable, t.Any]):
        """
        :param newly_decorated_object: The wrapped object from inner.
        The defined function would then be the custom decorator
        defined by the consumer

        e.g. the inner_wrapped_object in the example below would be
        "decorated_function"

        @decorator
        def decorated_function(inputs):
            print(inputs)
        """

        @wraps(newly_decorated_object)
        def returned_obj(*decorator_args, **decorator_kwargs) -> t.Callable:
            """
            Arguments passed to the "decorated_function".
            Ideally, the number of arguments in the decorator should be identical
            to what was defined below. The API will also perform a type check to ensure
            that the arguments passed are identical to what was specified.
            E.g.

            @decorator(int)
            def decorated_function(inputs):
                print(inputs)

            - Argument passed to decorated_function must be an 'int' if type checking
            is set to True

            @decorated_function(10)
            def another_function():
                ... write your function code here ...

            :param decorator_args:
            :param decorator_kwargs:
            """
            print("-" * 100)
            print(f"decorator_to_construct: {newly_decorated_object},\n"
                  f"Decorated args: {decorator_args}, kwargs: {decorator_kwargs}\n"
                  f"Returned object: {returned_obj}")
            print("-" * 100)

            # Sanity checks
            # -----------------------------------

            # Decorator should have equal length of arguments as specified
            # by the template
            decorator_name = newly_decorated_object.__name__
            if len(decorator_args) != len(type_template_args):
                raise ValueError(f"Passed '{len(decorator_args)}' arguments --> {decorator_args} "
                                 f"to decorator: '{decorator_name}'. "
                                 f"Should have '{len(type_template_args)}' arguments "
                                 f"of type: {type_template_args}")

            # And arguments that correspond to the specified types ...
            for decorator_arg, target_type in zip(decorator_args, type_template_args):
                if not type(decorator_arg) == target_type:
                    raise TypeError(f"Passed invalid type: {type(decorator_arg)}. "
                                    f"Expected type: '{target_type}'")

            def another_inner_func(func: t.Callable):
                """
                TODO: Write comment for this code soon
                :param func:
                :return:
                """
                def return_func(*args, **kwargs):
                    # print(f"Func: {func.__name__}, newly_decorated_object: {newly_decorated_object.__name__}")
                    return newly_decorated_object(func, *decorator_args, *args, **decorator_kwargs, **kwargs)
                return return_func

            return another_inner_func

        return returned_obj

    return wrapper


def optional_args(wrapped_func: t.Callable = None,
                  **kw) -> t.Callable:
    """
    Create function with optional arguments
    :param wrapped_func: The function to be wrapped
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

            # Check if object is sliceable
            # Raise exception if the passed in object
            # does not support slicing
            try:
                return output[:limit]
            except:
                raise TypeError(f"Cannot slice object: {output}")

        return decorated_func

    return decorator
