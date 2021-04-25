import os
import sys
import copy
import types
from typing import Callable, Union, Dict
import inspect
from functools import wraps
import time as t
from collections import OrderedDict
from helper.properties import TimeProperty

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

    def trace(self, target: Union[Callable, object]) -> None:
        """
        Used for running the trace function
        Example:
            yeezy.debug()
            def test():
                print("hello world")
        :rtype:
        """
        pass

    def _add_debug(self, target) -> None:
        self._add_function(target, self.functions)

    def time(self,
             passed_func: Callable = None,
             path: str = None,
             log_interval: int = 1,
             truncate_from: int = 200):

        def decorator(func):
            print("troll: ", func)
            # Register the decorated function
            self._add_function(func, self.functions, self.time, TimeProperty)

            # TODO: Implement other options
            @wraps(func)
            def wrapper(*args, **kwargs):
                time_start = t.time()
                output = func(*args, **kwargs)
                time_elapsed = t.time() - time_start
                self.functions[func].update(time_elapsed)
                return output

            return wrapper

        if callable(passed_func):
            return decorator(passed_func)

        return decorator

    def print_debug_message(self, msg: str) -> None:
        if self.debug:
            print(msg)

    def _add_function(self, target_func, target_dict, decorator_fn, property):
        func_name = target_func.__name__
        if func_name in self.seen_func_names:
            print(f"Function {func_name} already is decorated with " 
                  f"{decorator_fn.__name__}(). Is this intentional?")
        else:
            self.seen_func_names.add(func_name)

        # Add decorator to function methods
        if inspect.isclass(target_func):
            for func in dir(target_func):
                if callable(getattr(target_func, func)) and not func.startswith("__"):
                    target_dict[func] = property()
                    print("Found class: ", target_dict[func])

        elif callable(target_func):
            if target_func in target_dict:
                raise FunctionAlreadyAddedError(f"Function already added. Name: {target_func.__name__}")
            target_dict[target_func] = property()
        else:
            # print(inspect.stack()[1][3])  # will give the caller of foos name, if something called foo
            # TODO: Write a method for adding exceptions flexibly
            raise NotClassOrCallableError(f"Object: {target_func} is not a class object or callable")

    def create_class_decorator(self, callable_func: Callable) -> Callable:
        return util.ClassDecorator(callable_func)

    def __repr__(self) -> str:
        return "Yee ... yeezy :)"

    def profile(self) -> None:
        """
        Profile all the registered stuff
        :return:
        :rtype:
        """
        print(f"Printing time-related functions ... ")
        for func, properties in self.time_dict.items():
            print(f"Function: {func.__name__}, properties: {properties}")
        print("-" * 100)
        print("Printing registered functions")

        for func, properties in self.functions.items():
            print(func)
            print(f"Function: {func.__name__}, properties: {properties}")


if __name__ == "__main__":
    yee = Yeezy(__name__, debug=True)


    def register(self):
        """
        :param decorator_func: The function to decorate
        :param args: Argument
        :param kwargs: Kwargs
        :return:
        """
        # print(f"Name: {decorator_func.__name__}")
        # if decorator_func in self.custom:
        #     print(f"Warning: decorator name already exist ... Overwriting ...")
        # print(f"Registering new function: {decorator_func.__name__}")
        #
        # # Register to dictionary
        # self._add_function(decorator_func, self.custom)
        def decorator(decorator_func):
            print(f"Name: {decorator_func.__name__}")
            if decorator_func in self.custom:
                print(f"Warning: decorator name already exist ... Overwriting ...")
            print(f"Registering new function: {decorator_func.__name__}")

            # Register to dictionary
            self._add_function(decorator_func, self.custom)

            @wraps(decorator_func)
            def wrapper(*args, **kwargs):
                print(f"args: {args}. Kwargs: {kwargs}")
                output = decorator_func(*args, **kwargs)
                return output

            setattr(self, decorator_func.__name__, wrapper)

            return wrapper
        return decorator

    def do_before_do_go():
        print("before do_go()")


    @yee.time
    class Test:
        def __init__(self):
            self.test = [1, 2, 3]

        def mutate(self, num):
            self.test.append(num)

        def print_something(self, test):
            print(test)

        def create_long_list(self, n=1000000, name="test"):
            return list(range(n)), name


    def print_something(name):
        print(name)
        num = 10
        # yee.debug(num)

    @yee.time
    def do_go(num: list):
        print(f"yee registered running")

    @yee.time
    def create_long_list(n = 1000000, name="test"):
        return list(range(n)), name

    # create_long_list = yee.double_wrap(create_long_list)
    tom = Test()
    for i in range(10):
        create_long_list(10000000)
        tom.create_long_list(100)


    print_something("teemo")
    print("-" * 100)

    # Profile and gather information
    yee.profile()
