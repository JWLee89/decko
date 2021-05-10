"""
Author: Jay Lee
Decko: A decorator-based application for experimentation,
development and debugging.
Users can also dynamically decorate functions at runtime
which helps performance.

Basic use case:

yee = Decko()

@yee.trace
def buggy_function(input_1, input_2, ...):
    ...

# Analyze the function
yee.analyze()

"""
import cProfile
import copy
import inspect
import logging
import os
import pstats
import sys
from collections import OrderedDict
from functools import wraps
from typing import Callable, Dict, List, Union, Type

# Local imports
from .helper import exceptions
from .helper import util
from .helper.util import get_unique_func_name


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


class CustomFunction(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def _check_if_class(cls):
    if not util.is_class_instance(cls):
        raise exceptions.NotClassException("Yeezy.observe() observes only classes. "
                                           f"{cls} is of type: {type(cls)}")


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
        'compute_statistics': (bool, True),
    })

    CLASS_PROPS = OrderedDict({
        'prefix_filter': (str, ('_', '__'))
    })

    def __init__(self,
                 module_name: str,
                 root_path: str = None,
                 inspect_mode: int = InspectMode.PUBLIC_ONLY,
                 debug: bool = False,
                 log_path: str = None):

        #: The name of the package or module that this object belongs
        #: to. Do not change this once it is set by the constructor.
        self.module_name = module_name

        #: Absolute path to the package on the filesystem. Used to look
        #: up resources contained in the package.
        self.root_path = self.get_root_path() if root_path is None else root_path

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
        # E.g. "do_work" -- <Callable>
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
        self.log = util.logger_factory(module_name, log_also_to_console=True) if log_path else \
            util.logger_factory(module_name, file_name=log_path, log_also_to_console=True)

        # Initialize cProfiler
        self._profiler = cProfile.Profile()

        # TODO: Create parallel decorator for parallel processing

    def pure(self,
             event_cb: Callable = None,
             **kw) -> Callable:
        """
        Check to see whether a given function is pure.
        Note: Purity is determined purely by examining object interactions.
        This function will not check for I/O to determine purity.
        :param event_cb: The callback function raised when impurity is discovered.
        :param kw:
        :return:
        """
        undefined_event_cb = event_cb is None

        # Raise exception by default if modified.
        if undefined_event_cb:
            def event_cb(argument_name, before, after):
                raise exceptions.MutatedReferenceError(
                    f"Original input modified: {argument_name}. Before: {before}, "
                    f"after: {after}"
                )

        def wrapper(function: Union[Type, Callable]):

            @wraps(function)
            def inner(*args, **kwargs):
                # Creating deep copies can be very inefficient, especially
                # in our case where we have extremely large tensors
                # that take up a lot of space ...
                print("inner called")
                # TODO: Come up with a better way of checking
                input_data = util.get_shallow_default_arg_dict(function, args)
                original_input = copy.deepcopy(input_data)
                # Get output of function
                output = function(*args, **kwargs)
                # check inputs
                for key, value in input_data.items():
                    # If value has been modified, fire event!
                    if value != original_input[key]:
                        before = original_input[key]
                        after = input_data[key]
                        event_cb(key, before, after)

                return output

            self._decorate(self.pure, inner)

            # TODO: Abstract this logic
            if util.is_class_instance(function):
                return function

            return inner
        return wrapper

    def _add_class_decorator_rule(self, decorator_func: Callable,
                                  cls, **kwargs) -> None:
        """
        If the decorated object is a class, we will add different rules.
        For example, these rules include which types of functions to decorate
        TODO
        :param cls: The class we are decorating
        :param kwargs:
        :return:
        """
        properties: Dict = util.create_properties(Decko.CLASS_PROPS, **kwargs)
        # Filter all methods starting with prefix. If Filter is None or '',
        # will grab all methods
        filter_prefixes = properties['prefix_filter']
        for member_key in dir(cls):
            # We want to filter out certain methods such as dunder methods
            if callable(getattr(cls, member_key)) and not member_key.startswith(filter_prefixes):
                print(f"Decorating: {member_key}")
                # Get the class method and decorate
                fn: Callable = getattr(cls, member_key)
                decorated_function = self._decorate(decorator_func, fn)
                setattr(cls, member_key, decorated_function)

    def _add_function_decorator_rule(self,
                                     decorator_func: Callable,
                                     func: Callable, **kwargs) -> None:
        """
        Add common metadata regarding the decorated function.
        :param decorator_func:
        :param func:
        :param kwargs:
        :return:
        """
        properties: Dict = util.create_properties(Decko.FUNCTION_PROPS, **kwargs)
        self._update_decoration_info(decorator_func, func, properties)

    def add_decorator_rule(self,
                           decorator_func: Callable,
                           obj_to_decorate: Union[Callable, Type],
                           **kwargs) -> None:
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

        :param obj_to_decorate: The object to decorate. Can either be
        class instance or a function.
        :param kwargs: Keyword args added to decorator
        :return:
        """
        if util.is_class_instance(obj_to_decorate):
            self._add_class_decorator_rule(decorator_func ,
                                           obj_to_decorate, **kwargs)
        else:
            self._add_function_decorator_rule(decorator_func,
                                              obj_to_decorate, **kwargs)

    @staticmethod
    def get_new_configs(debug: bool,
                        inspect_mode: int,
                        log_path: str) -> Dict:
        """
        Creates set of new configurations, which determine the behavior of
        a Yeezy instance.
        :return: A configuration dictionary
        """
        new_config: OrderedDict = copy.deepcopy(Decko.DEFAULT_CONFIGS)
        # Override with user_inputs
        new_config['debug'] = debug
        new_config['inspect_mode'] = inspect_mode
        new_config['log_path'] = log_path
        return new_config

    def get_root_path(self) -> str:
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
            self.log_debug(f"||||||| You probably did not profile any functions or "
                           f"overwrote the function that was intended to be profiled. "
                           f"Check your code |||||||\nStacktrace: {ex}", logging.ERROR)

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
            self.log(msg, logging_type)

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

    def _decorate(self, decorator_func: Callable, func: Callable) -> Callable:
        """
        Common function for decorating functions such as registration
        :param func:
        :return:
        """
        # Decorate the function
        self.add_decorator_rule(decorator_func, func)

        @wraps(decorator_func)
        def wrapped(*args, **kwargs):
            print(inspect.getsource(func))
            return decorator_func(*args, **kwargs)
        return wrapped

    def fire_if(self,
                events_to_fire: List[Callable],
                predicate: Callable = lambda x: x) -> Callable:
        """
        Given a list of subscribed callables and an predicate function,
        create a wrapper that fires events when predicates are fulfilled

        >> Code sample
        ----------------------------------

        yee = Yeezy(__name__)

        def do_something(output, instance, arr):
            print(f"Output: {output}. Triggered by array: {arr}")


        @yee.fire_if([do_something], lambda x, arr: len(arr) > 5)
        def do_something(arr):
            return sum(arr)

        if __name__ == "__main__":
            # This should fire an event since we called
            test = do_something([1, 2, 3, 4, 5, 6])
            print(do_something([20, 30]))

        >> End code sample
        ----------------------------------

        :param events_to_fire: The subscribed events that will be triggered
        when predicate is true
        :param predicate: The condition for triggering the event
        :return: The wrapped function
        """

        def wrap(func: Callable) -> Callable:

            @wraps(func)
            def wrapped(*args, **kwargs):
                # Whatever function we are wrapping
                output = func(*args, **kwargs)
                fire_event = predicate(output, self, *args, **kwargs)
                # tell everyone about change based on predicate
                if fire_event:
                    for event in events_to_fire:
                        event(output, *args, **kwargs)
                return output

            return wrapped

        return wrap

    def profile(self, func: Callable) -> Callable:
        """
        Profile all instances
        :param func:
        :type func:
        :return:
        :rtype:
        """

        @wraps(func)
        def wrapped(*args, **kwargs):
            self._profiler.enable()
            output = func(*args, **kwargs)
            self._profiler.disable()
            return output

        return wrapped

    # def observe(self,
    #             properties: Union[Tuple, List] = None) -> Callable:
    #     """
    #     Observe properties in a class and log when they are being updated.
    #     :param properties: The properties to observe.
    #     """
    #
    #     is_list_or_tuple: bool = isinstance(properties, (list, tuple))
    #     is_class: bool = util.is_class_instance(properties)
    #
    #     def observe_class(cls):
    #         _check_if_class(cls)
    #         cls_name: str = f'{cls.__module__}.{cls.__name__}'
    #         class_props: List = [item for item in inspect.getmembers(cls) if not inspect.ismethod(item)]
    #         # Observe passed properties
    #         if is_list_or_tuple:
    #             # Go through all properties
    #             for prop in properties:
    #                 if prop not in class_props:
    #                     raise ValueError(f"Property '{prop}' not found in class <{cls_name}>.\n"
    #                                      f"Available props: {class_props}")
    #                 # Must pass in string
    #                 elif not isinstance(prop, str):
    #                     raise ValueError("Properties passed to .observe() should be a string. "
    #                                      f"Passed in value '{prop}' of type: {type(prop)}")
    #                 else:
    #                     pass
    #                     # property_value = cls.__getitem__(prop)
    #                     # print(f"Prop value: {property_value}")
    #
    #         # Observe all properties
    #         else:
    #             pass
    #
    #     # Called without calling decorator. e.g.
    #     # @yee.observe instead of @yee.observe()
    #     if is_class:
    #         return observe_class(properties)
    #     return observe_class

    def register(self,
                 func_name: str,
                 func: Callable,
                 function_map: Dict):
        """
        Register function
        :param func_name: The name of the function to register
        :param func: The function to register
        :param function_map: The dictionary to register the function to.
        Performs lookup based on function type
        :return:
        """
        if func_name not in function_map:
            function_map[func_name] = func

    def register_decorator(self,
                           func: Callable) -> bool:
        """
        Public API - Register the decorator as a decko custom method
        :param func: The function to register
        :return:
        """
        name: str = get_unique_func_name(func)
        function_exists: bool = name in self.custom
        if not function_exists:
            self.custom[name] = func

        return function_exists

    def _update_decoration_info(self,
                                decorator_func,
                                func_to_decorate: Callable,
                                props: Dict) -> None:
        # Common function for handling duplicates
        func_name: str = get_unique_func_name(func_to_decorate)
        decorator_func_name: str = get_unique_func_name(decorator_func)
        if func_name in self.functions:
            # Check if function is already decorated with same decorator
            registered_decorators: List = self.functions[func_name][API_KEYS.DECORATED_WITH]
            if decorator_func_name in registered_decorators:
                self.handle_error(f"Found duplicate decorator with identity: {func_name}",
                                  exceptions.DuplicateDecoratorError)
            else:
                registered_decorators.append(decorator_func_name)
        else:
            # Register new function
            self.functions[func_name] = {
                API_KEYS.FUNC_NAME: func_name,
                API_KEYS.FUNCTION: func_to_decorate,
                API_KEYS.PROPS: props,
                API_KEYS.DECORATED_WITH: [decorator_func_name]
            }
            # Add message if set to debug
        self.log_debug(f"Decorated function with unique id: {func_name}")

    def run_before(self, functions: Union[List[Callable], Callable], **kw):
        """
        This allows users to wrap a function without registering
        :param functions: A function or a list of functions that
        will be executed prior
        """
        if util.is_iterable(functions):
            def preprocess(funcs, *args, **kwargs):
                for f in funcs:
                    f(*args, **kwargs)
        else:
            def preprocess(func, *args, **kwargs):
                func(*args, **kwargs)

        def wrapper(fn: Callable) -> Callable:

            # Add basic decoration
            fn: Callable = self._decorate(self.run_before, fn)

            @wraps(fn)
            def inner(*args, **kwargs):
                util.fill_default_kwargs(fn, args, kwargs)
                preprocess(functions, *args, **kwargs)
                return fn(*args, **kwargs)
            return inner
        return wrapper

    # def stopwatch(self,
    #               passed_func: Callable = None,
    #               register: bool = True,
    #               path: str = None,
    #               log_interval: int = 1,
    #               truncate_from: int = 200):
    # 
    #     def decorator(func):
    #         self._decorate(self.stopwatch, func)
    # 
    #         # # Initialize input
    #         # self.functions[func_name][API_KEYS.STATS_INPUT] = 0
    # 
    #         @wraps(func)
    #         def wrapper(*args, **kwargs):
    #             time_start = time.time()
    #             output = func(*args, **kwargs)
    #             time_elapsed = time.time() - time_start
    #             # TODO: Find a way to salvage this again
    #             # self.functions[func_name][API_KEYS.STATS_INPUT] = time_elapsed
    #             # # Compute statistics
    #             # self.functions[func_name][API_KEYS.PROPS].update(time_elapsed)
    #             return output
    # 
    #         return wrapper
    #         # @wraps(func)
    #         # def wrapper(*args, **kwargs):
    #         #     time_start = t.time()
    #         #     output = func(*args, **kwargs)
    #         #     time_elapsed = t.time() - time_start
    #         #     print(f"Original func: {original_func}, name: {func.__name__}")
    #         #     # Compute statistics
    #         #     self.functions[original_func].update(time_elapsed)
    #         #     return output
    #         #
    #         # # Return original class without wrapping
    #         # if inspect.isclass(func):
    #         #     # Register the decorated function
    #         #     self._register_class(func, self.functions, self.time, TimeProperty)
    #         #     return func
    #         # else:
    #         #     # Register the decorated function
    #         #     self._register_object(original_func, original_func.__name__, self.functions, self.time, TimeProperty)
    #         #     return wrapper
    # 
    #     if callable(passed_func):
    #         return decorator(passed_func)
    # 
    #     return decorator

    def _register_class(self,
                        class_definition: object,
                        target_dict,
                        decorator_fn: Callable,
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
        return f"decko"

    # def analyze(self) -> None:
    #     """
    #     Profile all the registered stuff
    #     :return:
    #     :rtype:
    #     """
    #     self.log(f"Printing time-related functions ... ")
    #     self.log("-" * 100)
    #     for func, properties in self.time_dict.items():
    #         self.log(f"Function: {func.__name__}, properties: {properties}")
    #     self.log("-" * 100)
    #     self.log("Printing registered functions")
    #     self.log("-" * 100)
    #     for func_name, properties in self.functions.items():
    #         self.log(f"Function: {func_name}, properties: {properties}")
    #     self.log("-" * 100)


if __name__ == "__main__":
    dk = Decko(__name__, debug=True)


    @dk.pure(print)
    @dk.profile
    def input_output_what_how(a, b, c=[]):
        c.append(10)
        return c


    item = []
    output = input_output_what_how(10, 20, item)
    yee = input_output_what_how(10, 20, item)
    print(f"yee: {yee}")


    @dk.profile
    def long_list(n=100000):
        return list(range(n))


    for i in range(10):
        long_list()
    #
    stats = pstats.Stats(dk._profiler).sort_stats('ncalls')
    stats.print_stats()
