import sys
import os
from typing import Callable, Union
from exceptions import (
    NotClassOrCallable,
)
import inspect


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

    # TODO: Add default configurations in this section

    def __init__(self,
                 root_path: str = os.getcwd(),
                 inspect_mode: int = InspectMode.PUBLIC_ONLY):

        #: Absolute path to the package on the filesystem. Used to look
        #: up resources contained in the package.
        self.root_path = root_path
        self.inspect_mode = inspect_mode

        # Dictionary mapping function names to debug functions
        # E.g. "do_work" -- <Callable>
        self.debug_functions = {}

        # Dictionary of custom decorators added by users
        # Warning: do not modify this dictionary as it may cause unexpected behaviors
        self.custom_decorators = {}

        # List of classes to observe / profile
        self.class_observable = {}

        self.function_observables = {}

    def debug(self, target: Union[Callable, object]) -> None:
        """
        Used for running the trace function
        Example:
            yeezy.debug()
            def test():
                print("hello world")
        :rtype:
        """
        if inspect.isclass(target):
            method_list = [func for func in dir(target) if
                           callable(getattr(target, func)) and not func.startswith("__")]
            print(f"Methods: {method_list}")
        elif callable(target):
            self._add_function(target)
        else:
            # print(inspect.stack()[1][3])  # will give the caller of foos name, if something called foo
            # TODO: Write a method for adding exceptions flexibly
            raise NotClassOrCallable(f"Object: {target} is not a class object or callable")

    def _add_class(self, target: Union[Callable, ]):
        """

        :param target:
        :return:
        :rtype:
        """
        pass

    def _add_function(self, target):
        pass

    def register(self, decorator_name, *args, **kwargs):
        if decorator_name in self.custom_decorators:
           print(f"Warning: decorator name already exist ... Overwriting ...")

    def __repr__(self) -> str:
        return "Yee ... yeezy :)"

    def profile(self) -> None:
        """
        Profile all the registered stuff
        :return:
        :rtype:
        """
        pass


if __name__ == "__main__":
    yee = Yeezy()

    @yee.debug
    class Test:
        def __init__(self):
            self.test = [1, 2, 3]

        def mutate(self, num):
            self.test.append(num)


    def print_something(name):
        print(name)
        num = 10
        yee.debug(num)

    yee.debug(print_something)

    print_something("teemo")


