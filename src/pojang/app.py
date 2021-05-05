"""
Author: Jay Lee
Pojang: A decorator-based application for experimentation,
development and debugging.
Users can also dynamically decorate functions at runtime
which helps performance.

Basic use case:

yee = Pojang()

@yee.trace
def buggy_function(input_1, input_2, ...):
    ...

# Analyze the function
yee.analyze()

"""
import os
import sys
import copy
from typing import Callable, Dict, List, Tuple, Union
import inspect
from functools import wraps
import time
from collections import OrderedDict
import tracemalloc
from multiprocessing import Process

# Local imports
from src.pojang.helper.properties import TimeStatistics, Statistics
from src.pojang.helper.util import get_unique_func_name
from src.pojang.helper import util
import src.pojang.exceptions as exceptions


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


class CustomFunction(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def _check_if_class(cls):
    if not util.is_class_instance(cls):
        raise exceptions.NotClassException("Yeezy.observe() observes only classes. "
                                           f"{cls} is of type: {type(cls)}")


class Pojang:
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
    FUNCTION_PROPS = OrderedDict({
        'no_side_effect': (bool, False),
        'compute_statistics': (bool, True),
    })

    def __init__(self,
                 module_name: str,
                 root_path: str = None,
                 inspect_mode: int = InspectMode.PUBLIC_ONLY,
                 debug: bool = False,
                 log_path: str = None,
                 no_side_effects: bool = False):

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
        self.log = util.logger_factory(log_path, module_name) if log_path else print

        # Will raise an error if the wrapped function raises side_effect
        # Note: This behavior can be changed at runtime and also overridden
        # for each function
        self.no_side_effects = no_side_effects

    # TODO: Create parallel decorator for parallel processing

    def trace_memory(self, func):
        tracemalloc.start()

        @wraps(func)
        def inner(*args, **kwargs):
            snapshot1 = tracemalloc.take_snapshot()
            output = func(*args, **kwargs)
            # ... call the function to profile
            snapshot2 = tracemalloc.take_snapshot()
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')

            print("[ Top 10 differences ]")
            for stat in top_stats[:10]:
                print(stat)
            return output

        return inner

    def _add_class_decorator_rule(self, cls, **kwargs) -> None:
        """
        If the decorated object is a class, we will add different rules.
        For example, these rules include which types of functions to decorate
        :param cls: The class we are decorating
        :param kwargs:
        :return:
        """
        pass

    def _add_function_decorator_rule(self, func: Callable, **kwargs) -> None:
        properties = {}
        # Validate and add properties
        for key, (data_type, default_value) in Pojang.FUNCTION_PROPS.items():
            if key in kwargs:
                util.validate_type(kwargs, key, data_type)
                properties[key] = kwargs[key]
            else:
                properties[key] = default_value

        # Register the function
        func_name = get_unique_func_name(func)
        self._update_decoration_info(func_name, func)

        # Add message if set to debug
        self.log_debug(f"Function: {func_name} registered ... ")

    def add_decorator_rule(self, obj_to_decorate, **kwargs) -> None:
        """
        Add common rules to registered decorator which includes
        the following options:
            - kwargs:
        :param obj_to_decorate:
        :param kwargs:
        :return:
        """
        if util.is_class_instance(obj_to_decorate):
            self._add_class_decorator_rule(obj_to_decorate, **kwargs)
        else:
            self._add_function_decorator_rule(obj_to_decorate, **kwargs)

    @staticmethod
    def get_new_configs(debug: bool,
                        inspect_mode: int,
                        log_path: str) -> Dict:
        """
        Creates set of new configurations, which determine the behavior of
        a Yeezy instance.
        :return: A configuration dictionary
        """
        new_config = copy.deepcopy(Pojang.DEFAULT_CONFIGS)
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
        import_name = self.module_name
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
            raise TypeError("Yeezy.debug must be set to either True or False. "
                            f"Set to value: {new_mode} of type {type(new_mode)}")
        self.config['debug'] = new_mode

    # --------------------------
    # ----- Public Methods -----
    # --------------------------

    def log_debug(self, msg) -> None:
        """
        Print debug message if mode is set to
        debug mode
        :param msg: The message to log
        """
        if self.debug:
            self.log(f'DEBUG: {msg}')

    # Compute stats
    # @util.compute_stats()
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

    def observe(self,
                properties: Union[Tuple, List] = None) -> Callable:
        """
        Observe properties in a class and log when they are being updated.
        :param properties: The properties to observe.
        """

        is_list_or_tuple = isinstance(properties, (list, tuple))
        is_class = util.is_class_instance(properties)

        def observe_class(cls):
            _check_if_class(cls)
            cls_name = f'{cls.__module__}.{cls.__name__}'
            class_props = [item for item in inspect.getmembers(cls) if not inspect.ismethod(item)]
            print(f"Props: {class_props}, {dir(cls)}")

            # Observe passed properties
            if is_list_or_tuple:
                # Go through all properties
                for prop in properties:
                    if prop not in class_props:
                        raise ValueError(f"Property '{prop}' not found in class <{cls_name}>.\n"
                                         f"Available props: {class_props}")
                    # Must pass in string
                    elif not isinstance(prop, str):
                        raise ValueError("Properties passed to .observe() should be a string. "
                                         f"Passed in value '{prop}' of type: {type(prop)}")
                    else:
                        pass
                        # property_value = cls.__getitem__(prop)
                        # print(f"Prop value: {property_value}")

            # Observe all properties
            else:
                pass

        # Called without calling decorator. e.g.
        # @yee.observe instead of @yee.observe()
        if is_class:
            return observe_class(properties)
        return observe_class

    def trace(self,
              warn_side_effects=True,
              truncate_from: int = 100):
        """
        :param truncate_from: When handling large inputs,
        truncates the input so that log files
        do not become too large.
        """

        def inner_function(func):
            # Update function statistics
            func_name = get_unique_func_name(func)
            self.log_debug(f"Decorated function with unique id: {func_name}")
            self._update_decoration_info(func_name, func, Statistics(func))

            # Get arguments
            argspecs = inspect.getfullargspec(func)

            # call context variables
            caller_frame_record = inspect.stack()[1]
            caller_code = caller_frame_record.code_context[0].strip()

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return inner_function

    def _add_debug(self, target) -> None:
        self._register_object(target, self.functions)

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
        Public API - Register the decorator as a pojang custom method
        :param func: The function to register
        :return:
        """
        name = get_unique_func_name(func)
        function_exists = name in self.custom
        if not function_exists:
            self.custom[name] = func

        return function_exists

    def _register(self, func: Callable) -> None:
        """
        Handle registration of a function. Is
        applied to all functions
        :param func:
        :return:
        """
        func_name = get_unique_func_name(func)
        # TODO: register function
        self._update_decoration_info(func_name, func)
        self.log_debug(f"Function: {func_name} registered ... ")

    def before(self,
               func: Callable,
               stat_updater: Callable = None) -> Callable:
        """
        Create decorator that executes the function prior to
        the decorated function being executed
        :param func: The function to execute before the decorated function
        :stat_updater: If defined, statistics will be computed and updated
        after each execution.
        :param stat_updater:

        """
        func_name = get_unique_func_name(func)
        # register function
        self._update_decoration_info(func_name, func)
        self.log_debug(f"Function: {func_name} registered ... ")

        if stat_updater:
            @wraps(func)
            def inner(*args, **kwargs):
                output = func(*args, **kwargs)
                # TODO: Update statistical computation logic
                self.functions[func_name]['props'].update(
                    self.functions[func_name][API_KEYS.STATS_INPUT], *args, **kwargs)
                return output
        else:
            @wraps(func)
            def inner(*args, **kwargs):
                output = func(*args, **kwargs)
                print(self.functions[func_name])
                if API_KEYS.STATS_INPUT in self.functions[func_name]:
                    self.functions[func_name][API_KEYS.PROPS].update(
                        self.functions[func_name][API_KEYS.STATS_INPUT], *args, **kwargs)
                return output

        return inner

    def _update_decoration_info(self,
                                func_name: str,
                                func: Callable,
                                props: Statistics) -> None:
        # Common function for handling duplicates
        if func_name in self.functions:
            self.log_debug(f"Found duplicate decorator with identity: {func_name}")
        else:
            self.functions[func_name] = {
                API_KEYS.FUNC_NAME: func_name,
                API_KEYS.FUNCTION: func,
                API_KEYS.PROPS: props
            }

    def run_before(self, functions: Union[List[Callable], List]):
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

        def wrapper(fn):

            @wraps(fn)
            def inner(*args, **kwargs):
                preprocess(functions, *args, **kwargs)
                output = fn(*args, **kwargs)
                return output
            return inner
        return wrapper

    def stopwatch(self,
                  passed_func: Callable = None,
                  register: bool = True,
                  path: str = None,
                  log_interval: int = 1,
                  truncate_from: int = 200):

        def decorator(func):
            # Update function statistics
            func_name = get_unique_func_name(func)
            self.log(f"Decorated function with unique id: {func_name}")
            self._update_decoration_info(func_name, func, TimeStatistics(func))

            # Initialize input
            self.functions[func_name][API_KEYS.STATS_INPUT] = 0

            @wraps(func)
            def wrapper(*args, **kwargs):
                time_start = time.time()
                output = func(*args, **kwargs)
                time_elapsed = time.time() - time_start
                self.functions[func_name][API_KEYS.STATS_INPUT] = time_elapsed
                # Compute statistics
                self.functions[func_name][API_KEYS.PROPS].update(time_elapsed)
                return output

            return wrapper
            # @wraps(func)
            # def wrapper(*args, **kwargs):
            #     time_start = t.time()
            #     output = func(*args, **kwargs)
            #     time_elapsed = t.time() - time_start
            #     print(f"Original func: {original_func}, name: {func.__name__}")
            #     # Compute statistics
            #     self.functions[original_func].update(time_elapsed)
            #     return output
            #
            # # Return original class without wrapping
            # if inspect.isclass(func):
            #     # Register the decorated function
            #     self._register_class(func, self.functions, self.time, TimeProperty)
            #     return func
            # else:
            #     # Register the decorated function
            #     self._register_object(original_func, original_func.__name__, self.functions, self.time, TimeProperty)
            #     return wrapper

        if callable(passed_func):
            return decorator(passed_func)

        return decorator

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
        return f"pojang"

    def analyze(self) -> None:
        """
        Profile all the registered stuff
        :return:
        :rtype:
        """
        self.log(f"Printing time-related functions ... ")
        self.log("-" * 100)
        for func, properties in self.time_dict.items():
            self.log(f"Function: {func.__name__}, properties: {properties}")
        self.log("-" * 100)
        self.log("Printing registered functions")
        self.log("-" * 100)
        for func_name, properties in self.functions.items():
            self.log(f"Function: {func_name}, properties: {properties}")
        self.log("-" * 100)


if __name__ == "__main__":
    pj = Pojang(__name__, debug=True)

    def trigger_me(output, *args, **kwargs):
        print(f"Output: {output}.")

    @pj.stopwatch
    @pj.fire_if([trigger_me], lambda output, self, arr: len(arr) > 4)
    def do_something(arr):
        return sum(arr)

    def ding():
        print("ding")

    def dong():
        print("dong")

    @pj.trace_memory
    @pj.run_before([ding, dong])
    def dang():
        print("dang")

    # This should print "ding dong"
    dang()

    # This should fire an event since we called
    test = do_something([1, 2, 3, 4, 5, 6])
    do_something([20, 30])

    pj.analyze()
    print(pj)
