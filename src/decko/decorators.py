"""
Stateless version that provides only decorated functions.
This API will be consumed by users who want access
to decorator functions.
The bells and whistles such as state management
and debugging / profiling utilities will be provided
by each Decko instance.

TODO: Decide on which style of documentation to use
"""
import inspect
import traceback
import typing as t
from functools import wraps, partial
from time import process_time
import threading

from .helper.validation import (
    raise_error_if_not_class_instance,
)
from .helper.util import (
    create_instance,
    attach_property,
)

from .helper.exceptions import TooSlowError
from .immutable import ImmutableError
from types import MappingProxyType

# List of specific checks required when creating a decorator
__DECORATOR_SPECS__ = MappingProxyType({
    # By default, a type check is performed on decorators
    # to ensure that the defined functions meet specifications
    'enable_type_check': (bool, True),
})


def _set_defaults_if_not_defined(user_specs: t.Dict,
                                 default_specs: t.Mapping) -> None:
    """
    Update user_specs with default values if not specified.
    Also does a type check on user specifications to ensure
    that type validity and sanity is maintained.
    This modifies the original user_specs provided

    Args:
        user_specs (): The specifications provided by the user.
        This is updated with default specifications as needed.
        default_specs (): A dictionary of default specifications

    Returns:

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


def _handle_decorator_kwargs(type_template_args: t.Tuple,
                             type_template_kwargs: t.Dict,
                             decorator_args: t.Tuple,
                             decorator_kwargs: t.Dict) -> t.Tuple:
    """
    Two-step approach.
    1. Check if user specified kwarg value.
        - If the specified value is invalid (an empty tuple), we will raise an error
        - If a tuple of length 1 is specified, we will add object, since it can be of any type

    :param type_template_args: The type template
    :param type_template_kwargs: The type template
    :param decorator_args: The type template
    :param decorator_kwargs:
    :returns two tuples with newly added decorator values and types.
    """
    decorator_values, decorator_types = [], []

    # Merge
    for key, corresponding_values in type_template_kwargs.items():

        is_tuple = isinstance(corresponding_values, t.Tuple)
        is_non_empty_tuple = is_tuple and len(corresponding_values) > 0
        is_empty_tuple = is_tuple and len(corresponding_values) == 0
        use_default = key not in decorator_kwargs

        # by default, pass if any type
        types_to_check = object

        if is_empty_tuple:
            raise ValueError("Cannot provide non-empty tuple as default kwarg.")

        # Find value to append. If it is a tuple, we are targeting the first value
        if use_default and is_non_empty_tuple:
            value_to_append = corresponding_values[0]
            types_to_check = corresponding_values[1:]
        elif not is_tuple:
            value_to_append = corresponding_values
        else:
            value_to_append = decorator_kwargs[key]

        # Append to decorator value
        decorator_values.append(value_to_append)

        # Lastly append the types to check
        decorator_types.append(types_to_check)

    return tuple(list(decorator_args) + decorator_values), \
           tuple(list(type_template_args) + decorator_types)


def _handle_method(function_to_evaluate: t.Callable,
                   args: t.Tuple) -> t.Tuple:
    """
    This will return self or cls
    based on whether the given function is a

    - method - return self
    - classmethod - return cls

    Other methods will return None as the first item
    in the tuple

    Args:
        function_to_evaluate (t.Callable): The function to be evaluated
        *args (t.Tuple): Arguments passed by the consumer

    Returns:
        (t.Tuple): A two-tuple with the following specifications:
            - (self, *args) if func is a method
            - (cls, *args) if func is decorated with @classmethod
            - (None, *args) if func is a staticmethod or a function
        """
    # If tuple is empty, we do not even need to evaluate,
    # since classmethod or method has at least one argument
    if len(args):
        self_or_cls = args[0]
        # Bound methods can be accessed by cls_or_class.<name-of-method>
        method = getattr(self_or_cls, function_to_evaluate.__name__, None)
        if method:
            wrap = getattr(method, "__func__", None)
            original = getattr(wrap, "original", None)
            if original is function_to_evaluate:
                return self_or_cls, args[1:]
    return None, args


def deckorator(*type_template_args,
               is_class_decorator: bool = False,
               **type_template_kwargs):
    """
    Decorate a function based on its type.
    Decorators come in two forms:
        - Function decorators
        - Class decorators

    Args:
        *type_template_args ():

        These are used to define the data types
        that the decorator will be accepting. The type-safety ensures
        that the behavior of the decorator is more predictable, making it easier
        to write decorators whose behaviors are more predictable.

        A tuple can be used as a placeholder. This means that the argument
        can be an instance of two or more types.

        E.g.

        @deckorator((float, int), t.Callable)
        def new_decorator(wrapped_func,
                        float_or_int_arg,
                        callable_arg,
                        *args,
                        **kwargs):
            pass


        is_class_decorator (bool):

        Defaults to false. If set to true, we are specifying that the decorator created
        is designed to be a class decorator.

        **type_template_kwargs (): We also want users to be able to provide keyword
        args with default behaviors if not specified, which helps reduce boilerplate
        in some cases.

        if a keyword argument is passed, the provided value can be
        1. An object representing default value or
        2. A non-empty tuple

        In case of a tuple, the first item represents the default value and the
        following values represents the allowed types.
        In the example below, the keyword argument 'val' has a default value of '5'
        and can either be an instance of type int or float.

        E.g.

        @deckorator((float, int), callback=(print, t.Callable))
        def new_decorator(wrapped_func,
                        float_or_int_arg,
                        *args,
                        **decorator_kwargs,
                        **kwargs):
            callback = decorator_kwargs['callback']

        # callback does not need to be defined.
        @new_decorator(100)
        def function_to_decorate(arg1, arg2):
            ..

    Returns:

    """

    def inner(new_decorator_function: t.Callable):
        """

        Args:
            new_decorator_function ():

            The newly created decorator.

            e.g. "new_decorator_function" in the example below would be
            "new_decorator_function"

            @decorator
            def new_decorator_function(decorated_function,
                                        *args, **kwargs):
                pass
        """
        # Check if input function applies descriptor protocol
        desc = next((desc for desc in (staticmethod, classmethod)
                     if isinstance(new_decorator_function, desc)), None)

        # If static or class method, we know we can decorate it
        if desc:
            new_decorator_function = new_decorator_function.__func__
        # Otherwise, we need to check if it is a callable object ...
        elif not callable(new_decorator_function):
            raise TypeError("new_decorator_function must be callable ...")

        @wraps(new_decorator_function)
        def returned_func(*decorator_args,
                          **decorator_kwargs):
            """
            @deckorate(int)
            def new_decorator_function(wrapped_func,
                                        int_arg,
                                        *args, **kwargs):
                # The body of the function

            Args:
                *decorator_args (): The args object of the decorator.
                This is the actual value

                @deckorator(int)
                def new_decorator(wrapped_func,
                                     # an integer value.
                                     # Has a value of 10, which is set below
                                    int_arg,
                                    *args,
                                    **kwargs)

                @new_decorator(10)
                def add(a, b):
                    return a + b

                **decorator_kwargs (): The kwargs object of the decorator.

                e.g.

                @deckorator(kwarg_item="test")
                def new_decorator(wrapped_func,
                                    kwarg_item, # has value of "test"
                                    *args,
                                    **kwargs)

            Returns:

            """
            cls_or_self, new_args = _handle_method(new_decorator_function, decorator_args)
            # Place kwargs into decorator args (handle default values as well)
            decorator_args, type_template_arguments = _handle_decorator_kwargs(type_template_args,
                                                                               type_template_kwargs,
                                                                               new_args,
                                                                               decorator_kwargs)

            # Handle case where self or cls exists
            # TODO: Clean this code up
            if cls_or_self:
                def wrapped_func(wrapped_function: t.Callable):

                    wrapped_object_is_class = inspect.isclass(wrapped_function)
                    if is_class_decorator and not wrapped_object_is_class:
                        raise TypeError("Specified a class decorator, "
                                        f"but passed in object of type: {type(wrapped_function)}")

                    def final_func(*args, **kwargs):
                        return new_decorator_function(cls_or_self,
                                                      wrapped_function,
                                                      *decorator_args,
                                                      *args, **kwargs)
                    return final_func
            else:
                def wrapped_func(wrapped_object: t.Callable):

                    # Class decorator
                    wrapped_object_is_class = inspect.isclass(wrapped_object)
                    if is_class_decorator and not wrapped_object_is_class:
                        raise TypeError("Specified a class decorator, "
                                        f"but passed in object of type: {type(wrapped_object)}")

                    def final_func(*args, **kwargs):
                        return new_decorator_function(wrapped_object,
                                                      *decorator_args,
                                                      *args,
                                                      **kwargs)

                    return final_func

            num_of_decorator_args = len(decorator_args)
            # In case when called with zero args
            if num_of_decorator_args == 1 and not len(type_template_arguments):
                function_to_wrap = decorator_args[0]
                # set argument to empty afterwards
                decorator_args = ()
                return wrapped_func(function_to_wrap)

            # Ensure that number of type template args matches
            if num_of_decorator_args != len(type_template_arguments):
                decorator_name = new_decorator_function.__name__
                raise ValueError(f"Passed '{len(decorator_args)}' argument: '{decorator_args}' "
                                 f"to decorator: '{decorator_name}'. "
                                 f"Should have '{len(type_template_arguments)}' arguments "
                                 f"of type: {type_template_arguments}")

            # Then, perform validation to check whether
            # arguments are that of correspond to the specified types ...
            for decorator_arg, target_type in zip(decorator_args, type_template_arguments):
                if not isinstance(decorator_arg, target_type):
                    raise TypeError(f"Passed invalid type: {type(decorator_arg)}. "
                                    f"Expected type: '{target_type}'")
            return wrapped_func
            # return new_decorator_function(*decorator_args, **decorator_kwargs)

        # Used for sanity checking to make sure that
        # the method called is a method
        returned_func.original = new_decorator_function

        if desc:
            returned_func = desc(returned_func)
        return returned_func

    # Triggered when called as follows
    # @decorator instead of @decorator(...)
    if len(type_template_args) == 1 and inspect.isfunction(type_template_args[0]):
        # This is the wrapped function
        wrapped_function = type_template_args[0]
        # Since wrapped function is not a type template args,
        # set type_template_args to empty tuple
        type_template_args = ()
        return inner(wrapped_function)

    return inner


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

@deckorator(t.Callable)
def stopwatch(wrapped_func: t.Callable,
              callback: t.Callable = print,
              *args,
              **kwargs):
    start_time = process_time()
    output = wrapped_func(*args, **kwargs)
    time_elapsed = process_time() - start_time
    callback(time_elapsed)
    return output


@deckorator(t.Callable)
def execute_if(function_to_decorate: t.Callable,
               predicate: t.Callable,
               *args, **kwargs) -> t.Callable:
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
    :param function_to_decorate: Function decorated by this function
    :param predicate: The condition for triggering the event
    :return: The wrapped function
    """
    fire_event = predicate(*args, **kwargs)
    if fire_event:
        return function_to_decorate(*args, **kwargs)


def _default_slower_than_callback(time_elapsed, threshold_time):
    raise TooSlowError("Function took too long to run ... "
                       f"Should take less than {threshold_time} "
                       f"ms but took {time_elapsed} ms")


@deckorator((float, int), t.Callable)
def slower_than(wrapped_function: t.Callable,
                time_ms: float,
                callback: t.Callable,
                *args,
                **kwargs) -> t.Any:
    """
    Executes callback if time taken takes longer than specified time
    :param wrapped_function: The function that was wrapped.
    :param time_ms: If the function does not complete in specified time,
    :param callback: The function that is called if decorator is triggered
    a warning will be raised.
    """
    start = process_time() * 1000
    output = wrapped_function(*args, **kwargs)
    elapsed = (process_time() * 1000) - start
    if elapsed > time_ms:
        callback(elapsed, time_ms)
    return output


@deckorator(is_class_decorator=True)
def freeze(cls: t.Type[t.Any],
           *args, **kwargs) -> t.Type[t.Any]:
    """
    Completely freeze a class.
    A frozen class will raise an error if any of its properties
    are mutated or if new classes are added
    :param cls: A Class
    """
    def do_freeze(slf, name, value):
        msg = f"Class {type(slf)} is frozen. " \
              f"Attempted to set attribute '{name}' to value: '{value}'"
        raise ImmutableError(msg)

    class Immutable(cls):
        """
        A basic immutable class
        """

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            setattr(Immutable, '__setattr__', do_freeze)

    return Immutable(*args, **kwargs)


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


@deckorator(t.Callable)
def filter_by_output(wrapped_func,
                     predicate: t.Callable,
                     *args, **kwargs) -> t.Any:
    """
    Return the value if it passes a predicate function.
    Else, return None.
    :param wrapped_func: The function that was wrapped
    :param predicate: The predicate function. If output is True,
    return the actual output.
    """
    output = wrapped_func(*args, **kwargs)
    if predicate(output):
        return output


@deckorator(t.Callable)
def raise_error_if(wrapped_function: t.Callable,
                   trigger_condition: t.Callable,
                   *args, **kwargs) -> t.Any:
    """
    Raise exception if a condition is met
    Args:
        wrapped_function (): The function that was wrapped
        trigger_condition (): A function that returns true when
        a certain condition is met. Otherwise, the error will not
        be raised.
    """
    output = wrapped_function(*args, **kwargs)
    if trigger_condition(output):
        raise RuntimeError(f"{raise_error_if.__name__}({trigger_condition.__name__}) "
                           "triggered because condition was met.\n"
                           f"Wrapped function: '{wrapped_function.__name__}()' "
                           f"yielded output value {output}")


@deckorator(int)
def truncate(wrapped_function: t.Callable,
             limit: int,
             *args, **kwargs) -> t.Callable:
    """
    Truncate a slice-able object
    :param wrapped_function: The function that was wrapped
    :param limit: The maximum size of the target object
    """
    output: t.Union[str, t.List, t.Tuple] = wrapped_function(*args, **kwargs)
    try:
        return output[:limit]
    except Exception:
        raise TypeError(f"Cannot slice object: {output}")


@deckorator(t.Tuple, t.Callable, raise_error=(False, bool))
def try_except(wrapped_func: t.Callable,
               errors_to_catch: t.Tuple[Exception],
               error_callback: t.Callable,
               raise_error: bool = False,
               *args, **kwargs):
    """
    Wraps the entire function around a try-catch block and
    catches the exception.
    :param wrapped_func: The function that was wrapped
    :param errors_to_catch: A tuple of exceptions to catch
    :param error_callback: The error callback to call when exception is caught
    :param raise_error: If set to true, after handling error_callback, an error will
    be raised.
    """
    try:
        return wrapped_func(*args, **kwargs)
    except errors_to_catch as error:
        tb = traceback.format_exc()
        error_callback(error, tb)
        if raise_error:
            raise
