import os
import copy
from typing import Callable, Union, Dict
import inspect
from functools import wraps
import time as t
from collections import OrderedDict

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
    PRIVATE = 1
    PUBLIC_ONLY = 2


class Yeezy:
    """
    Yeeeee ....
    Entry point of the application.
    Architected as follows:

    -
    """

    # This is where default configurations are located
    #
    DEFAULT_CONFIGS = {

    }

    def __init__(self,
                 root_path: str = os.getcwd(),
                 inspect_mode: int = InspectMode.PUBLIC_ONLY,
                 debug: bool = False):

        #: Absolute path to the package on the filesystem. Used to look
        #: up resources contained in the package.
        self.root_path = root_path
        self.inspect_mode = inspect_mode
        self.bool = debug

        # Dictionary mapping function names to debug functions
        # E.g. "do_work" -- <Callable>
        self.functions = OrderedDict()

        # Dictionary of custom decorators added by users
        # Warning: do not modify this dictionary as it may cause unexpected behaviors
        self.custom_decorators = OrderedDict()

        # timing-related properties
        self.time_dict = OrderedDict()

        # Create default configs
        self.config = self.get_new_configs()

    @staticmethod
    def get_new_configs() -> Dict:
        """
        Creates set of new configurations, which determine the behavior of
        a Yeezy instance.
        :return: A configuration dictionary
        """
        new_config = copy.deepcopy(Yeezy.DEFAULT_CONFIGS)
        return new_config
    # ------------------------
    # ------ Properties ------
    # ------------------------

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

        def inner_function(func):
            self._add_function(func, self.functions)
            if func not in self.time_dict:
                self.time_dict[func] = {}
            time_dict = self.time_dict[func]

            # State variables
            time_dict['count'] = 0
            time_dict['accumulated_time'] = 0

            @wraps(func)
            def wrapper(*args, **kwargs):
                # TODO: Don't repeat key
                time_dict['count'] += 1
                start_time = t.time()
                output = func(*args, **kwargs)
                time_dict['accumulated_time'] += (t.time() - start_time)
                return output
            return wrapper

        # Make func callable
        if callable(passed_func):
            return inner_function(passed_func)

        return inner_function

    @staticmethod
    def _add_function(target_func, target_dict):

        if inspect.isclass(target_func):
            for func in dir(target_func):
                if callable(getattr(target_func, func)) and not func.startswith("__"):
                    target_dict[func] = func
                    print(f"Function: {func.__name__} added")

        elif callable(target_func):
            if target_func in target_dict:
                raise FunctionAlreadyAddedError(f"Function already added. Name: {target_func.__name__}")
            target_dict[target_func] = target_func
        else:
            # print(inspect.stack()[1][3])  # will give the caller of foos name, if something called foo
            # TODO: Write a method for adding exceptions flexibly
            raise NotClassOrCallableError(f"Object: {target_func} is not a class object or callable")

    def register(self, decorator_func):
        """
        :param decorator_func: The function to decorate
        :param args: Argument
        :param kwargs: Kwargs
        :return:
        """
        print(f"Name: {decorator_func.__name__}")
        if decorator_func in self.custom_decorators:
            print(f"Warning: decorator name already exist ... Overwriting ...")
        print(f"Registering new function: {decorator_func.__name__}")
        self._add_function(decorator_func, self.custom_decorators)

        @wraps(decorator_func)
        def wrapper(*args, **kwargs):
            output = decorator_func(*args, **kwargs)
            return output
        return wrapper

    def create_class_decorator(self, callable_func: Callable) -> Callable:
        return util.ClassDecorator(callable_func)

    def __repr__(self) -> str:
        return "Yee ... yeezy :)"

    def _do_profile(self):
        pass

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

        for func, properties in self.custom_decorators.items():
            print(f"Function: {func.__name__}, properties: {properties}")


if __name__ == "__main__":
    yee = Yeezy()

    def do_before_do_go():
        print("before do_go()")

    @yee.trace
    class Test:
        def __init__(self):
            self.test = [1, 2, 3]

        def mutate(self, num):
            self.test.append(num)

        @yee.trace
        def print_something(self, test):
            print(test)


    def print_something(name):
        print(name)
        num = 10
        # yee.debug(num)


    @yee.register
    def do_go(num: list):
        num.append("item")


    @yee.time()
    def create_long_list(n = 1000000, name="test"):
        return list(range(n)), name

    # create_long_list = yee.double_wrap(create_long_list)

    for i in range(10):
        create_long_list(10000000)

    print_something("teemo")
    print("-" * 100)

    # Profile and gather information
    yee.profile()