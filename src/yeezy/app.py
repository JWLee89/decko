"""
Author: Jay Lee
Yeezy: A decorator-based application for experimentation,
development and debugging.
Users can also dynamically decorate functions at runtime
which helps performance.

Basic use case:

yee = Yeezy()

@yee.trace
def buggy_function(input_1, input_2, ...):
    ...

# Analyze the function
yee.analyze()

"""
import os
import sys
import copy
from typing import Callable, Dict
import inspect
from functools import wraps
import time as t
from collections import OrderedDict


try:
    from .helper.properties import TimeStatistics, Statistics
    from .helper.util import get_unique_func_name
    from .exceptions import (
        NotClassOrCallableError,
        FunctionAlreadyAddedError,
    )
    from .helper import util
except Exception:
    from helper.properties import TimeStatistics, Statistics
    from helper.util import get_unique_func_name
    # prevent ImportError: attempted relative import with no known parent package
    from exceptions import (
        NotClassOrCallableError,
        FunctionAlreadyAddedError,
    )
    from helper import util


def get_class_that_defined_method(meth):
    for cls in inspect.getmro(meth.im_class):
        if meth.__name__ in cls.__dict__:
            return cls
    return None


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


class Yeezy:
    """
    Yeeeee ....
    Entry point of the application.
    Architected as follows:

    -
    """

    # Properties utilized by Yeezy
    DEFAULT_CONFIGS = OrderedDict({
        'debug': False,
        'inspect_mode': InspectMode.PUBLIC_ONLY,
        'log_path': None
    })

    def __init__(self,
                 import_name: str,
                 root_path: str = None,
                 inspect_mode: int = InspectMode.PUBLIC_ONLY,
                 debug: bool = False,
                 log_path: str = None):

        #: The name of the package or module that this object belongs
        #: to. Do not change this once it is set by the constructor.
        self.import_name = import_name

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
        self.log = util.logger_factory(log_path, "yeezy") if log_path else print

    @staticmethod
    def get_new_configs(debug: bool,
                        inspect_mode: int,
                        log_path: str) -> Dict:
        """
        Creates set of new configurations, which determine the behavior of
        a Yeezy instance.
        :return: A configuration dictionary
        """
        new_config = copy.deepcopy(Yeezy.DEFAULT_CONFIGS)
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
        import_name = self.import_name
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

    # --------------------------
    # ----- Public Methods -----
    # --------------------------

    def log_debug(self, msg) -> None:
        if self.debug:
            self.log(msg)

    def trace(self,
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

            # State variables
            count = {func: 0}
            debug_properties = {}

            # call context variables
            caller_frame_record = inspect.stack()[1]
            caller_code = caller_frame_record.code_context[0].strip()
            debug_properties['call_signature'] = caller_code

            @wraps(func)
            def wrapper(*args, **kwargs):
                debug_properties = {}

                caller_frame_record = inspect.stack()[1]
                caller_code = caller_frame_record.code_context
                debug_properties['call_context'] = f"Called {caller_code[0].strip()} on line no: " \
                                                   f"{caller_frame_record.lineno} from {caller_frame_record.filename}"
                self.log(f"{debug_properties['call_context']}")
                # Update state variables
                count[func] += 1

                args_repr = [repr(a) for a in args]  # 1
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
                default_index = 0
                warning_str = ''
                function_input_str = f"Debug: {caller_code[0].strip().split('(')[0]}("
                i = 0
                for test in argspecs.args:
                    if i < len(args):
                        value = args_repr[i]
                    elif i >= len(args) and test not in kwargs:
                        value = argspecs.defaults[default_index]
                        default_index += 1
                    else:
                        value = kwargs[test]

                    function_input_str += f"{test}={value}"
                    function_input_str += ','
                    function_input_str += ' '
                    i += 1

                # remove trailing ', ' --> Handle edge case where function accepts zero arguments
                function_input_str = function_input_str[:-2] if i > 0 else function_input_str

                function_input_str += f') called {count[func]} times.'
                self.log(function_input_str)

                deep_cpy_args = copy.deepcopy(args)
                original_kwargs = copy.deepcopy(kwargs)

                # Now check of side-effects
                value = func(*args, **kwargs)
                truncated_str_output = str(value)[:truncate_from] + ' ...'

                for i in range(len(args)):
                    before, after = deep_cpy_args[i], args[i]
                    if before != after:
                        print(f"Argument at index: {i} has been modified!: {before} --> {after}")

                for key in kwargs.keys():
                    before, after = original_kwargs[key], kwargs[key]
                    if before != after:
                        print(f"Argument at index: {i} has been modified!: {before} --> {after}")

                self.log(truncated_str_output)  # 4
                debug_properties['output'] = truncated_str_output
                debug_properties['return_type'] = type(value)
                self.log(f"Return type: {type(value)}")

                return value

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
        if func not in function_map:
            function_map[func_name] = func

    def register_decorator(self,
                           func: Callable) -> bool:
        """
        Public API - Add decorators
        :param func: The function to register
        :return:
        """
        name = get_unique_func_name(func)
        function_exists = name in self.custom
        if not function_exists:
            self.custom[name] = function_exists

        return function_exists

    def _register(self, func: Callable) -> Callable:
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

    def time(self,
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
                time_start = t.time()
                output = func(*args, **kwargs)
                time_elapsed = t.time() - time_start
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
        return "Yee ... yeezy :)"

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
