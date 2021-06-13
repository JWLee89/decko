"""
Author: Jay Lee
Decko: A decorator-based application for experimentation,
development and debugging.
Users can also dynamically decorate functions at runtime
which helps performance.

Basic use case:

dk = Decko()

@dk.trace
def buggy_function(input_1, input_2, ...):
    ...

# Analyze the function
dk.analyze()

TODO: Write out specifications for each of the functions
1. Function-based decorator specifications

`1.1. Register Decorators
`1.2. Accepts two inputs
    - decorator_func: The property / feature to add to the function to decorate
    - func_to_decorate: The target function that will be decorated
    - kw: dictionary containing user inputs and options.

2. Class-based decorator specifications

 2.1. Register Decorators
 2.2. Accepts two inputs
    - class_to_decorate: The class to decorate
        - Inspect properties:


TODO: Find a way to combine statistics of all decorated functions
-> Allow both global and contextual management of decorators

TODO: Add common function for handling callbacks if it exists.
TODO: Add a utility function for creating
    1. No arg decorator
    2. Decorator with arguments
    3. Decoration with context manager
"""
import cProfile
import copy
import inspect
import logging
import os
import pstats
import sys
import threading
from time import process_time
from collections import OrderedDict
from functools import wraps
import typing as t

# Local imports
from .helper import exceptions
from .helper import util
from .helper.validation import (
    raise_error_if_not_class_instance,
)
from .helper.validation import is_class_instance, is_iterable
from .helper.util import get_unique_func_name
from .immutable import ImmutableError
from .decorators import (
    deckorator,
)


class InspectMode:
    ALL = 0
    PUBLIC_ONLY = 1
    PRIVATE_ONLY = 2


class API_KEYS:
    # Properties
    PROPS = 'props'
    STATS_INPUT = 'input'
    FUNC_NAME = 'name'
    FUNCTION = 'func'
    DECORATED_WITH = 'decorated_with'

    # Used with callback
    CALLBACK = 'callback'


class CustomFunction(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


__lock__ = threading.RLock()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._locked_call(*args, **kwargs)
        return cls._instances[cls]

    # @synchronized(__lock__)
    def _locked_call(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)


class DeckoState(metaclass=Singleton):
    """
    Manage the state of the decko application
    """
    def __init__(self):
        self.functions = OrderedDict()

    def __repr__(self):
        return ", ".join([f'{function_name}: {v}' for function_name, v in self.functions.items()])


class Decko:
    """
    Yeeeee ....
    Entry point of the application.
    Architected as follows: Note: TODO
    -
    """

    # Properties utilized by Yeezy
    DEFAULT_CONFIGS = OrderedDict({
        'debug': False,
        'inspect_mode': InspectMode.PUBLIC_ONLY,
        'log_path': None
    })

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

    # These are the required types and default properties of class-based decorators
    CLASS_PROPS = OrderedDict({
        'prefix_filter': (str, ('_', '__'))
    })

    def __init__(self,
                 module_name: str,
                 root_path: str = None,
                 inspect_mode: int = InspectMode.PUBLIC_ONLY,
                 debug: bool = False,
                 log_path: str = None,
                 register_globally = True):

        #: The name of the package or module that this object belongs
        #: to. Do not change this once it is set by the constructor.
        self.module_name = module_name

        #: Absolute path to the package on the filesystem. Used to look
        #: up resources contained in the package.
        self.root_path = self._get_root_path() if root_path is None else root_path

        # Inspection Mode:
        # Note that this only inspection targets that are classes and not functions
        # ALL: 0 - Inspect all functions regardless of their access modifiers
        # PUBLIC_ONLY: 1 - Inspect only public methods
        # PRIVATE_ONLY: 2 -Inspect only "underscore methods" e.g. def _do_something(self, ...)
        self.inspect_mode = inspect_mode

        #: Absolute path to the package on the filesystem. Used to look
        #: up resources contained in the package.
        self.root_path = root_path

        # Dictionary mapping function names to debug functions
        # E.g. "do_work" -- <t.Callable>
        self.functions = OrderedDict()

        # Dictionary of custom decorators added by users
        # Warning: do not modify this dictionary as it may cause unexpected behaviors
        self.custom = CustomFunction()

        # timing-related properties
        self.time_dict = OrderedDict()

        # Create default configs dictating behavior of application
        # during runtime
        self.config = self.get_new_configs(debug, inspect_mode, log_path)

        # Logging function
        # If not specified, the default fallback method will be print()
        self.log = util.logger_factory(module_name, file_name=log_path) if log_path else \
            util.logger_factory(module_name)

        # Initialize cProfiler
        self._profiler = cProfile.Profile()

        # If set to true, stats can be examined globally, even from different files.
        self.register_globally = register_globally

        # Register globally
        self.global_state = DeckoState()

    def pure(self, **kw) -> t.Callable:
        """
        Check to see whether a given function is pure.
        Note: Purity is determined purely by examining object interactions.
        This function will not check for I/O to determine purity.
        :return: A wrapped function that checks whether the function mutates its input variables.
        Will handle callback if mutation is detected.
        """

        def wrapper(func: t.Union[t.Type, t.Callable]):
            # Decorate with common properties such as debug log messages
            # And registration
            # func: t.Callable = self._decorate_func(self.pure, func, **kw)

            # Raise exception by default if modified.
            if API_KEYS.CALLBACK not in kw:
                def event_cb(argument_name, before, after):
                    raise exceptions.MutatedReferenceError(
                        f"Original input modified: {argument_name}. Before: {before}, "
                        f"after: {after}"
                    )
            else:
                event_cb = kw[API_KEYS.CALLBACK]

            @wraps(func)
            def inner(*args, **kwargs):
                # Creating deep copies can be very inefficient, especially
                # in our case where we have extremely large tensors
                # that take up a lot of space ...
                input_data = util.get_shallow_default_arg_dict(func, args)
                original_input = copy.deepcopy(input_data)
                # Get output of function
                output = func(*args, **kwargs)
                # check inputs
                for key, value in input_data.items():
                    # If we are comparing objects
                    # Assumes that people name the first object self
                    if key == 'self':
                        for k in value.__dict__.keys():
                            value = getattr(value, k)
                            original_value = getattr(original_input['self'], k)
                            if value != original_value:
                                event_cb(k, original_value, value)
                    # If value has been modified, fire event!
                    elif value != original_input[key]:
                        before = original_input[key]
                        after = input_data[key]
                        event_cb(key, before, after)

                return output

            self.add_decorator_rule(self.pure, func, **kw)
            # TODO: Abstract this logic
            if is_class_instance(func):
                return func

            return inner

        return wrapper

    def _add_class_decorator_rule(self,
                                  decorator_func: t.Callable,
                                  cls, **kwargs) -> None:
        """
        If the decorated object is a class, we will add different rules.
        For example, these rules include which types of functions to decorate
        TODO: Find better way of creating debug messages
        :param cls: The class we are decorating
        :param kwargs:
        :return:
        """
        properties: t.Dict = util.create_properties(Decko.CLASS_PROPS, **kwargs)
        # Filter all methods starting with prefix. If Filter is None or '',
        # will grab all methods
        dashes = '-' * 100
        msg = []
        if self.debug:
            msg.append(f"\n{dashes}\nDecorating class <{cls.__name__}> ...")
        filter_prefixes = properties['prefix_filter']
        for member_key in dir(cls):
            member_variable = getattr(cls, member_key)
            # We want to filter out certain methods such as dunder methods
            if callable(member_variable) and not member_key.startswith(filter_prefixes):
                if self.debug:
                    msg.append(f"Decorating: {get_unique_func_name(member_variable)}() "
                               f"with function: {get_unique_func_name(decorator_func)}()")
                # Get the class method and decorate
                decorated_function = self._decorate_func(decorator_func, member_variable)
                setattr(cls, member_key, decorated_function)

        if self.debug:
            msg.append(dashes)
        self.log_debug('\n'.join(msg))
        return cls

    def _add_function_decorator_rule(self,
                                     decorator_func: t.Callable,
                                     func: t.Callable, **kwargs) -> None:
        """
        Add common metadata regarding the decorated function.
        :param decorator_func:
        :param func:
        :param kwargs:
        :return:
        """
        properties: t.Dict = util.create_properties(Decko.FUNCTION_PROPS, **kwargs)
        self._update_decoration_info(decorator_func, func, properties)

    def add_decorator_rule(self,
                           decorator_func: t.Callable,
                           obj_to_decorate: t.Union[t.Callable, t.Type],
                           **kwargs):
        """
        Add common rules to registered decorator which includes
        the following options:
            - kwargs:
        :param decorator_func: The decorator function applied to
        obj_to_decorate.

        E.g.

        @decorator_func
        def obj_to_decorate():
            pass


        :param wrap_with:
        :param obj_to_decorate: The object to decorate. Can either be
        class instance or a function.
        :param kwargs: Keyword args added to decorator
        :return:
        """
        if is_class_instance(obj_to_decorate):
            return self._add_class_decorator_rule(decorator_func,
                                                  obj_to_decorate, **kwargs)
        self._add_function_decorator_rule(decorator_func, obj_to_decorate, **kwargs)

    @staticmethod
    def get_new_configs(debug: bool,
                        inspect_mode: int,
                        log_path: str) -> t.Dict:
        """
        Creates set of new configurations, which determine the behavior of
        the current instance.
        :return: A configuration dictionary
        """
        new_config: OrderedDict = copy.deepcopy(Decko.DEFAULT_CONFIGS)
        # Override with user_inputs
        new_config['debug'] = debug
        new_config['inspect_mode'] = inspect_mode
        new_config['log_path'] = log_path
        return new_config

    def _get_root_path(self) -> str:
        """
        Find the root path of a package, or the path that contains a
        module. If it cannot be found, returns the current working directory.
        """
        import_name: str = self.module_name
        # Module already imported and has a file attribute. Use that first.
        mod = sys.modules.get(import_name)

        if mod is not None and hasattr(mod, "__file__"):
            return os.path.dirname(os.path.abspath(mod.__file__))

        return os.getcwd()

    # ------------------------
    # ------ Properties ------
    # ------------------------

    @property
    def debug(self) -> bool:
        return self.config['debug']

    @debug.setter
    def debug(self, new_mode):
        if type(new_mode) != bool:
            raise TypeError("Decko.debug must be set to either True or False. "
                            f"Set to value: {new_mode} of type {type(new_mode)}")
        self.config['debug'] = new_mode

    # --------------------------
    # ----- Public Methods -----
    # --------------------------

    def print_profile(self, sort_by: str = 'ncalls') -> None:
        try:
            stats = pstats.Stats(self._profiler).strip_dirs().sort_stats(sort_by)
            stats.print_stats()
        except TypeError as ex:
            self.log_debug(f"||||||| You probably did not profile t.Any functions or "
                           f"overwrote the function that was intended to be profiled. "
                           f"Check your code.\nStacktrace: {ex}", logging.ERROR)

    def dump_profile(self, file_path: str, sort_by: str = 'ncalls'):
        stats = pstats.Stats(self._profiler).strip_dirs().sort_stats(sort_by)
        stats.dump_stats(file_path)

    def log_debug(self, msg: str, logging_type: int = logging.DEBUG) -> None:
        """
        Print debug message if mode is set to
        debug mode
        :param msg: The message to log
        :param logging_type: The logging type as specified
        in the logging module
        """
        if self.debug:
            self.log(' ' + msg, logging_type)

    def handle_error(self,
                     msg: str,
                     error_type) -> None:
        """
        Log the error to the console and file, and also raise an exception
        :param msg: The message to display
        :param error_type: The type of error to raise. E.g. ValueError()
        """
        self.log(msg, logging.ERROR)
        raise error_type(msg)

    def _decorate_func(self,
                       decorator_func: t.Callable,
                       func: t.Callable,
                       **kw) -> t.Callable:
        """
        Common function for decorating functions such as registration
        And adding debug messages if decko is being run on debug mode.
        Note: For performance, in order to run debug, the function must be
        decorated with debug set to true. Otherwise, the function will not log
        t.Any messages.

        Decoration is as follows:

        --------------------------
        @dk.pure()
        def i_am_decorated(a, b):
            ...

        decorator_func: dk.pure
        func = i_am_decorated
        --------------------------

        :param decorator_func: The decorator function that will be applied
        :param func: The function to decorate.
        :return:
        """
        # Register the function and add appropriate metadata
        self._add_function_decorator_rule(decorator_func, func, **kw)

    def execute_if(self,
                   predicate: t.Callable) -> t.Callable:
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
        def wrap(func: t.Callable) -> t.Callable:
            @wraps(func)
            def wrapped(*args, **kwargs):
                fire_event = predicate(*args, **kwargs)
                if fire_event:
                    return func(*args, **kwargs)

            self.add_decorator_rule(self.execute_if, func)

            return wrapped

        return wrap

    @deckorator((float, int), callback=(None, t.Callable))
    def slower_than(self,
                    wrapped_func: t.Callable,
                    time_ms: t.Union[float, int],
                    callback: t.Callable,
                    *args, **kwargs):
        """
        Raise a warning if time taken takes longer than
        specified time
        :param time_ms: If the function does not complete in specified time,
        a warning will be raised.
        :param kw: Additional
        :return:
        :rtype:
        """
        func_name = get_unique_func_name(wrapped_func)
        start = process_time() * 1000
        output = wrapped_func(*args, **kwargs)
        elapsed = (process_time() * 1000) - start
        self.log_debug(f"Function {func_name} called. Time elapsed: "
                       f"{elapsed} milliseconds.")
        if elapsed > time_ms:
            if callback:
                callback(time_ms)
            else:
                self.log(f"Function: {func_name} took longer than"
                         f"{time_ms} milliseconds. Total time taken: {elapsed}",
                         logging.WARNING)
        self.add_decorator_rule(self.slower_than, wrapped_func)
        return output

    def instance_data(self,
                      filter_predicate: t.Callable = None,
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
            inst = util.create_instance(cls, *arguments)

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
                        util.attach_property(cls, prop, getter, setter)

            # Now, decorate each method with
            return ObservableClass

        return wrapper

    def freeze(self, cls: t.Type[t.Any]) -> t.Type[t.Any]:
        """
        Completely freeze a class.
        A frozen class will raise an error if t.Any of its properties a
        :param cls:
        :return:
        :rtype:
        """

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

    def immutable(self, cls, filter_predicate=None):
        """
        Create immutable classes with properties.
        :param filter_predicate: The predicate condition for creating immutable properties
        :param cls: The class we are decorating. Ultimately, the properties of the target
        class is decorated.
        """

        def raise_value_error(cls_instance, new_val):
            raise ValueError(f"Cannot set immutable property of type {type(cls_instance)} "
                             f"with value: {new_val}")

        return self.instance_data(filter_predicate, setter=raise_value_error)(cls)

    def profile(self, func: t.Callable) -> t.Callable:
        """
        Profile target functions with default cProfiler.
        For multi-threaded programs, it is recommended to use
        yappy.
        :param func: The function to profile
        :return: wrapped function with profiling logic
        """

        @wraps(func)
        def wrapped(*args, **kwargs):
            self._profiler.enable()
            output = func(*args, **kwargs)
            self._profiler.disable()
            return output

        self.add_decorator_rule(self.profile, func)
        return wrapped

    def _update_decoration_info(self,
                                decorator_func,
                                func_to_decorate: t.Callable,
                                props: t.Dict) -> None:
        # Common function for handling duplicates
        func_name: str = get_unique_func_name(func_to_decorate)
        decorator_func_name: str = get_unique_func_name(decorator_func)
        if func_name in self.functions:
            # Check if function is already decorated with same decorator
            registered_decorators: t.List = self.functions[func_name][API_KEYS.DECORATED_WITH]

            # If decorated, we disallow duplicate decorator since it serves no purpose
            if decorator_func_name in registered_decorators:
                self.handle_error(f"Found duplicate decorator with identity: {func_name}",
                                  exceptions.DuplicateDecoratorError)

            # If the actual function is different, we allow
            # Plus, we don't need to register. We just simply add to the list of decorated function
            else:
                registered_decorators.append(decorator_func_name)
        else:
            # Register new function Locally
            self.functions[func_name] = {
                API_KEYS.FUNCTION: func_to_decorate,
                API_KEYS.PROPS: props,
                API_KEYS.DECORATED_WITH: [decorator_func_name]
            }

            # Add to global state
            self.global_state.functions[func_name] = self.functions[func_name]

        # Add message if set to debug
        self.log_debug(f"Decorated {func_name} with: {decorator_func_name}")

    def run_before(self,
                   functions: t.Union[t.List[t.Callable], t.Callable],
                   **kw):
        """
        This allows users to wrap a function without registering
        :param functions: A function or a t.List of functions that
        will be executed prior
        """
        if is_iterable(functions):
            def preprocess(funcs, *args, **kwargs):
                for f in funcs:
                    f(*args, **kwargs)
        else:
            def preprocess(func, *args, **kwargs):
                func(*args, **kwargs)

        def wrapper(fn: t.Callable) -> t.Callable:

            # Add basic decoration
            @wraps(fn)
            def inner(*args, **kwargs):
                util.fill_default_kwargs(fn, args, kwargs)
                preprocess(functions, *args, **kwargs)
                return fn(*args, **kwargs)

            fn: t.Callable = self._decorate_func(self.run_before, fn)
            return inner

        return wrapper

    def trace(self,
              obj,
              **kw):
        def wrapper(func):
            func_name: str = get_unique_func_name(func)
            if API_KEYS.CALLBACK in kw and callable(kw[API_KEYS.CALLBACK]):
                callback = kw[API_KEYS.CALLBACK]
            else:
                callback = self.log_debug

            @wraps(func)
            def race(*args, **kwargs):
                callback(f"Function: {func_name}() called with args: {args}, kwargs: {kwargs}")
                return func(*args, **kwargs)

            return race

        self.add_decorator_rule(self.trace, wrapper, obj, **kw)
        if callable(obj):
            return wrapper(obj)
        if inspect.isclass(obj):
            return obj
        return wrapper

    def _register_class(self,
                        class_definition: object,
                        target_dict,
                        decorator_fn: t.Callable,
                        property_obj) -> None:
        """
        Scan through class and add all related classes
        """
        for item in dir(class_definition):
            if callable(getattr(class_definition, item)) and not item.startswith("__"):
                # Get the class method
                fn = getattr(class_definition, item)
                # Add name in front of method
                fn_name = f"{class_definition.__name__}.{fn.__name__}"

                # TODO: Register the function
                # self._register_object(fn, fn_name, target_dict, decorator_fn, property_obj)

                # # Decorate function and update method
                # we already registered above
                decorated_func = decorator_fn(fn)
                setattr(class_definition, item, decorated_func)

    def __repr__(self) -> str:
        return f"decko: {self.functions}"
