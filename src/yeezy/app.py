import os
import sys
import copy
import types
from typing import Callable, Union, Dict, List
import inspect
from functools import wraps
import time as t
from collections import OrderedDict
from helper.properties import TimeProperty, Test as Troll, create_long_list as cll
import logging

try:
    from .exceptions import (
        NotClassOrCallableError,
        FunctionAlreadyAddedError,
    )
    from .helper import util
except:
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


def write_file(file_name: str,
               logger_name: str,
               level=logging.INFO) -> Callable:
    """
    Function for writing information to a file during program execution
    :param file_name: The name of the file to store log
    :param logger_name: The name of the function being called
    :param level: The debug level
    """
    file_handler = logging.FileHandler(file_name, 'a')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                  '%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger = logging.getLogger(logger_name)

    for hdlr in logger.handlers[:]:  # remove all old handlers
        logger.removeHandler(hdlr)
    logger.addHandler(file_handler)  # set the new handler

    def write(contents_to_write: Union[str, List]) -> None:
        """
        When utilizing this function, please note that file I/O is relatively costly,
        so try calling this function at the end of creating a message string
        :param contents_to_write: The contents to append to the target log file.
        """
        logger.warning(contents_to_write)

    return write


def truncate(max_length: int) -> Callable:
    """
    Responsible for truncating a sentence based on its length
    :param max_length:
    :return: a truncation function
    """
    def do_truncate(sentence: str) -> str:
        truncated_sentence = (sentence[:max_length], ' ...') if len(sentence) > max_length else sentence
        return truncated_sentence
    return do_truncate


class InspectMode:
    ALL = 0
    PUBLIC_ONLY = 1
    PRIVATE_ONLY = 2


class Yeezy:
    """
    Yeeeee ....
    Entry point of the application.
    Architected as follows:

    -
    """

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
        self.custom = OrderedDict()

        # timing-related properties
        self.time_dict = OrderedDict()

        # Create default configs dictating behavior of application
        # during runtime
        self.config = self.get_new_configs(debug, inspect_mode, log_path)

        self.seen_func_names = set()

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

    def trace(self, silent: bool = True, path: str = None, truncate_from = 100):
        """
        :param silent: Silently accumulates statistics regarding the
        wrapped function called during the
        :param path: If specified, the log will be stored in the specified file.
        """

        def inner_function(func):
            count = {}
            # Get arguments
            argspecs = inspect.getfullargspec(func)

            # State variables
            count[func] = 0
            debug_properties = {}

            # call context variables
            caller_frame_record = inspect.stack()[1]
            caller_filename = caller_frame_record.filename
            caller_code = caller_frame_record.code_context[0].strip()
            debug_properties['call_signature'] = caller_code

            # Function that is used to write to certain file
            truncator = truncate(truncate_from)
            write_function = write_file(path, caller_filename) if path else print

            @wraps(func)
            def wrapper(*args, **kwargs):
                function_name = func.__name__
                debug_properties = {}

                caller_frame_record = inspect.stack()[1]
                caller_code = caller_frame_record.code_context
                debug_properties['call_context'] = f"Called {caller_code[0].strip()} on line no: " \
                                                   f"{caller_frame_record.lineno} from {caller_frame_record.filename}"
                print(f"{debug_properties['call_context']}")
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
                write_function(function_input_str)

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

                write_function(truncated_str_output)  # 4
                debug_properties['output'] = truncated_str_output
                debug_properties['return_type'] = type(value)
                print(f"Return type: {type(value)}")

                return value

            return wrapper

        return inner_function

    def _add_debug(self, target) -> None:
        self._register_object(target, self.functions)

    def _get_unique_func_name(self, func: Callable):
        return f'{func.__module__}.{func.__qualname__}'

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
        name = self._get_unique_func_name(func)
        function_exists = name in self.custom
        if not function_exists:
            self.custom[name] = function_exists

        return function_exists

    def decorate(self,
                 func_to_decorate: Callable):
        """
        :param func_to_decorate:
        :return:
        :rtype:
        """
        func_name = self._get_unique_func_name(func_to_decorate)
        # TODO: register function
        self.register(func_name, func_to_decorate, self.functions)
        print(f"Function: {func_name} registered ... ")

        @wraps(func_to_decorate)
        def inner(*args, **kwargs):
            # TODO: add behavior
            output = func_to_decorate(*args, **kwargs)

            # TODO: Compute statistics
            return output
        return inner

    def time(self,
             passed_func: Callable = None,
             register: bool = True,
             path: str = None,
             log_interval: int = 1,
             truncate_from: int = 200):

        def decorator(func):
            if func in self.functions:
                print("Found duplicate decorator: ", func.__name__)
            else:
                self.functions[func] = TimeProperty()

            @wraps(func)
            def wrapper(*args, **kwargs):
                time_start = t.time()
                output = func(*args, **kwargs)
                time_elapsed = t.time() - time_start
                # Compute statistics
                self.functions[func].update(time_elapsed)
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

    def print_debug_message(self, msg: str) -> None:
        if self.debug:
            print(msg)

    def _is_seen(self, name, decorated_fn):
        seen = name in self.seen_func_names
        if seen:
            print(f"Function {name} already is decorated with "
                  f"{decorated_fn.__name__}(). Is this intentional?")
        else:
            self.seen_func_names.add(name)
        return seen

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

                # Register the function
                self._register_object(fn, fn_name, target_dict, decorator_fn, property_obj)

                # # Decorate function and update method
                # we already registered above
                decorated_func = decorator_fn(fn)
                setattr(class_definition, item, decorated_func)

    def _register_object(self,
                         target,
                         fn_name,
                         target_dict,
                         decorator_fn,
                         property_obj):

        if callable(target):
            seen = self._is_seen(fn_name, decorator_fn)
            if seen:
                print(f"Function seen: ", fn_name)
            target_dict[target] = property_obj()
        else:
            raise NotClassOrCallableError(f"Object: {target} is not a class object or callable")

    def create_class_decorator(self, callable_func: Callable) -> Callable:
        return util.ClassDecorator(callable_func)

    def __repr__(self) -> str:
        return "Yee ... yeezy :)"

    def analyze(self) -> None:
        """
        Profile all the registered stuff
        :return:
        :rtype:
        """
        print(f"Printing time-related functions ... ")
        print("-" * 100)
        for func, properties in self.time_dict.items():
            print(f"Function: {func.__name__}, properties: {properties}")
        print("-" * 100)
        print("Printing registered functions")
        print("-" * 100)
        for func_name, properties in self.functions.items():
            print(f"Function: {func_name}, properties: {properties}")
        print("-" * 100)


if __name__ == "__main__":
    import torch
    yee = Yeezy(__name__, debug=True)

    def do_before_do_go():
        print("before do_go()")


    item = Troll()

    # This should register all functions inside of class Test()
    # @yee.time
    class Test:
        def __init__(self):
            self.test = [1, 2, 3]

        def mutate(self, num):
            self.test.append(num)

        def print_something(self, test):
            print(test)

        # @yee.trace()
        # @yee.time()
        @yee.decorate
        def create_long_list(self, n=1000000, name="test"):
            name = "troll"
            return torch.tensor(range(n))

    def print_something(name):
        print(name)
        num = 10
        # yee.debug(num)

    def do_go(num: list):
        print(f"yee registered running")

    def create_long_list(n = 1000000, name="test"):
        return list(range(n)), name

    # create_long_list = yee.double_wrap(create_long_list)
    tom = Test()

    # We can decorate methods using the following methods
    troll = Troll()
    another_fn = yee.decorate(troll.print_this)
    # Another create long list
    fn = cll
    # fn = yee.decorate(fn)
    # fn = yee.decorate(fn)

    for i in range(10):
        # tom.create_long_list(i)
        fn(i)
        create_long_list(100)
        # tom.create_long_list(1000)
        # tom.mutate(10)

    print("-" * 100)

    # Profile and gather information
    yee.analyze()
