"""
Stateless version that provides only decorated functions.
This API will be consumed by users who want access
to decorator functions.
The bells and whistles such as state management
and debugging / profiling utilities will be provided
by each Decko instance.

TODO: Update comments to google style
TODO: Move all non-core decorators out of this file and into separate files
based on their features.
This file will only hold the core building blocks used to create decorators.

"""
import inspect
import typing as t
from types import MappingProxyType
from functools import wraps, partial
from collections import OrderedDict, deque
from abc import ABC
from time import process_time
import threading

# Local imports
from .api import MODULE_METHOD_DECORATOR_API
from .helper.validation import (
    raise_error_if_not_class_instance,
    is_public_method,
)
from .helper.util import (
    create_instance,
    attach_property,
    create_properties,
)

from .helper.exceptions import TooSlowError, ImmutableError

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
               on_decorator_creation: t.Callable = None,
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

        on_decorator_creation (t.Callable):

        This function handles pre-processing logic that will run only once when
        creating the decorator. Useful for adding hooks or events to manage states
        when initializing decorators.

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
            # TODO: Clean up code and reduce boilerplate
            if cls_or_self:
                def wrapped_func(decorated_function: t.Callable):

                    wrapped_object_is_class = inspect.isclass(decorated_function)
                    if is_class_decorator and not wrapped_object_is_class:
                        raise TypeError("Specified a class decorator, "
                                        f"but passed in object of type: {type(decorated_function)}")

                    # If on_decorator_creation is defined
                    if isinstance(decorated_function, t.Callable) and isinstance(on_decorator_creation, t.Callable):
                        preprocessed_output = on_decorator_creation(cls_or_self,
                                                                    new_decorator_function,
                                                                    decorated_function,
                                                                    *decorator_args)

                        if preprocessed_output:
                            @wraps(decorated_function)
                            def final_func(*args, **kwargs):
                                return new_decorator_function(cls_or_self,
                                                              decorated_function,
                                                              *preprocessed_output,
                                                              *decorator_args,
                                                              *args,
                                                              **kwargs)

                            return final_func

                    @wraps(decorated_function)
                    def final_func(*args, **kwargs):
                        return new_decorator_function(cls_or_self,
                                                      decorated_function,
                                                      *decorator_args,
                                                      *args,
                                                      **kwargs)

                    return final_func
            else:
                def wrapped_func(wrapped_object: t.Callable):

                    # Class decorator
                    wrapped_object_is_class = inspect.isclass(wrapped_object)
                    if is_class_decorator and not wrapped_object_is_class:
                        raise TypeError("Specified a class decorator, "
                                        f"but passed in object of type: {type(wrapped_object)}")

                    # If on_decorator_creation is defined
                    # Eww ... Find way to
                    if isinstance(wrapped_object, t.Callable) and isinstance(on_decorator_creation, t.Callable):
                        preprocessed_output = on_decorator_creation(new_decorator_function,
                                                                    wrapped_object,
                                                                    *decorator_args)

                        @wraps(wrapped_object)
                        def final_func(*args, **kwargs):
                            return new_decorator_function(wrapped_object,
                                                          *preprocessed_output,
                                                          *decorator_args,
                                                          *args,
                                                          **kwargs)
                    else:
                        @wraps(wrapped_object)
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


class bind(partial):
    """
    An improved version of partial which accepts Ellipsis (...) as a placeholder
    """
    def __call__(self, *args, **keywords):
        keywords = {**self.keywords, **keywords}
        iargs = iter(args)
        args = (next(iargs) if arg is ... else arg for arg in self.args)
        return self.func(*args, *iargs, **keywords)


def register_object(self,
                    decorator_method: t.Callable,
                    function_to_decorate: t.Callable,
                    *args,
                    **kwargs):
    """
    Register object to the decko class.
    Used in conjunction with the @deckorate decorator
    to add functions to be observed with minimal boilerplate
    Args:
        self:
        decorator_method: The decorator function that was applied
        function_to_decorate: The function that will be decorated by decorator_function

    Returns:
        The decorated function that handles registration of the decorator to the decko instance.
    """
    method_name = decorator_method.__name__
    functions = self._functions
    if method_name in functions:
        functions[method_name][MODULE_METHOD_DECORATOR_API.DECORATED].append(function_to_decorate.__name__)
    else:
        raise ValueError("This should never happen. Programmer made a mistake")


def deckorate_method() -> t.Callable:
    """
    Add common metadata to functions and register
    the decorated function to keep track of its performance

    Returns:
        Decorator designed to register objects
    """
    return bind(deckorator, on_decorator_creation=register_object)


deckorate_method = deckorate_method()


def bind_method(instance, func, as_name=None):
    """
    Bind the function *func* to *instance*, with either provided name *as_name*
    or the existing name of *func*. The provided *func* should accept the
    instance as the first argument, i.e. "self".
    """
    if as_name is None:
        as_name = func.__name__
    bound_method = func.__get__(instance, instance.__class__)
    setattr(instance, as_name, bound_method)
    return bound_method


class Module(ABC):
    # Key value pairs of required properties
    # First element is the type of the keyword parameter
    # The second is the default value to assign
    FUNCTION_PROPS = OrderedDict({
        # Users can choose to not compute statistics
        # Or define their own statistics by calling a custom function
        # By definition, all statistics are dictionary values, which can be accessed or
        # printed during runtime.
        'compute_statistics': ([bool, t.Callable], True),
        # Callbacks can be specified to perform an event
        'callback': (t.Callable, None),
    })

    """
    A self-contained decko module which is used
    to manage decorator states.
    By default, all methods on the module are decorators and are used
    to wrap functions.
    All custom modules must extend this function
    """

    def __init__(self):

        # If set to true, the original
        # function is returned without decoration
        self.is_disabled = False

        # A list of functions along with corresponding states
        self._functions = OrderedDict()

        # Register the function
        self._register_public_methods()

        # list takes O(N) to remove from the front.
        self.event_queue = deque()

        # Unlimited size
        self.event_queue_size_limit = -1

    def _register_public_methods(self):
        """
        Register all public methods to compute and update state variables used for debugging.
        Returns:
            None. Updates the local state of the current module

        """
        public_methods = inspect.getmembers(self, predicate=is_public_method)
        for method_name, method in public_methods:
            self._register_method(method_name, method)

            def compute(func):
                @wraps(func)
                def inner(inner_self, *args, **kwargs):
                    print(f"timo tee : {args}, {func}")
                    output = func(*args, **kwargs)
                    print("yee")
                    return output
                return inner
            bind_method(self, compute(method))

    def _add_to_event_queue(self, msg: str) -> None:
        """
        Add message to event queue.
        Args:
            msg: The message to add. Can be something like
            "decorator has been successfully registered."
        """
        # limited
        size_limit = self.event_queue_size_limit
        current_size = len(self.event_queue)
        if current_size > size_limit:
            remove_up_to = size_limit - current_size
            while remove_up_to != 0:
                self.event_queue.popleft()

        # Lastly, add
        self.event_queue.append(msg)

    def _register_method(self,
                         method_name: str,
                         method: t.Callable):
        """
        Register function as a decorator
        Args:
            method_name: The name of the method
            method: The actual method object
        """
        # Register new function Locally
        self._functions[method_name] = {
            MODULE_METHOD_DECORATOR_API.METHOD: method,
            MODULE_METHOD_DECORATOR_API.DECORATED: [],
        }

    def __len__(self):
        """
        Returns:
            The number of decorators added to the function.
        """
        return len(self._functions.keys())

# --------------------------------------------
# ------------ Utility decorators ------------
# --------------------------------------------


@deckorator(t.Callable)
def execute_if(decorated_function: t.Callable,
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
    :param decorated_function: Function decorated by this function
    :param predicate: The condition for triggering the event
    :return: The wrapped function
    """
    fire_event = predicate(*args, **kwargs)
    if fire_event:
        return decorated_function(*args, **kwargs)


def _default_slower_than_callback(time_elapsed, threshold_time):
    raise TooSlowError("Function took too long to run ... "
                       f"Should take less than {threshold_time} "
                       f"ms but took {time_elapsed} ms")


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


def singleton(thread_safe: bool = True) -> t.Type[t.Any]:
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


@deckorator(int)
def truncate(decorated_function: t.Callable,
             limit: int,
             *args, **kwargs) -> t.Callable:
    """
    Truncate a slice-able object
    Args:
        decorated_function: The function that was wrapped
        limit: The maximum size of the target object
    Returns:
        A decorator that truncates the output of the wrapped function
    """
    output: t.Union[str, t.List, t.Tuple] = decorated_function(*args, **kwargs)
    try:
        return output[:limit]
    except Exception:
        raise TypeError(f"Output of function '{decorated_function.__name__()}' is not slice-able. "
                        f"Output: '{output}' ")
