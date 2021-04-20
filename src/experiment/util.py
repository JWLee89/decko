import copy
import time
import functools
from typing import List, Callable
import inspect
import sys


try:
    from contextlib import contextmanager
except ImportError:
    raise ImportError('cannot import contextmanager from contextlib. '
                      f'Current python version: {sys.version_info}. Requires version >= 3.2')


class TimeComputer:
    """
    Class for running experiments for computing the average time taken
    to perform computation over a series of N runs. Example:

    time_elapsed_ms = []
    for i in range(100):
        with TimeComputer(time_elapsed_ms) as tc:
            # Run experiment here
            items = list(range(100000))
     print(f"Avg time elapsed: {TimeComputer.compute_avg_time(time_elapsed_ms, unit=TimeComputer.Units.MS)}")
    """
    class Units:
        MS = 'milliseconds'

    def __init__(self, accumulated_time: List) -> None:
        if not isinstance(accumulated_time, list):
            raise TypeError(f"Accumulated_time must be a list. "
                            f"Passed in type: {type(accumulated_time)}")
        self.accumulated_time = accumulated_time

    def __enter__(self) -> None:
        self.start_time = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        time_elapsed = time.time() - self.start_time
        self.accumulated_time.append(time_elapsed)

    @staticmethod
    def compute_avg_time(time_list: List, unit: str = None) -> float:
        avg_time = sum(time_list) / len(time_list)
        if unit == TimeComputer.Units.MS:
            avg_time *= 1000
        return avg_time


class TraceDecorator:
    def __init__(self, func: Callable, verbose: bool = False):
        self.func = func
        self.verbose = verbose
        self.default_index = 0
        self.argspecs = inspect.getfullargspec(func)

    def __call__(self, *args, **kwargs):
        ...
        # use self.param1
        result = self.func(*args, **kwargs)
        # use self.param2
        return result

    def get_default_values(self, *args, **kwargs):
        args_repr = [repr(a) for a in args]  # 1
        default_index = 0
        function_input_str = "Debug: calling --> " + self.func.__name__ + '('
        for i, test in enumerate(args):
            if i < len(args):
                function_input_str += args_repr[i]
            elif i >= len(args) and test not in kwargs:
                function_input_str += f"{test}={self.argspecs.defaults[default_index]}"
                default_index += 1
            else:
                function_input_str += f"{test}={kwargs[test]}"
            # Add commas and space
            function_input_str += ','
            function_input_str += ' '

        # remove trailing ', '
        function_input_str = function_input_str[:-2]
        function_input_str += ')'
        return function_input_str


def trace(silent: bool = True, path: str = None):
    """
    :param silent: Silently accumulates statistics regarding the
    wrapped function called during the
    :param path: If specified, the log will be stored in the specified file
    """
    def inner_function(func, count={}):

        # Get arguments
        argspecs = inspect.getfullargspec(func)
        function_args = inspect.signature(func)

        # State variables
        count[func] = 0

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # Update state variables
            count[func] += 1


            args_repr = [repr(a) for a in args]  # 1
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
            default_index = 0
            warning_str = ''
            function_input_str = "Debug: " + func.__name__ + '('
            for i, test in enumerate(argspecs.args):
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

            # remove trailing ', '
            function_input_str = function_input_str[:-2]
            function_input_str += f') called {count[func]} times.'
            print(function_input_str)

            signature = ", ".join(args_repr + kwargs_repr)  # 3
            print(f"Calling {func.__name__}({signature})")


            deep_cpy_args = copy.deepcopy(args)
            deep_cpy_kwargs = copy.deepcopy(kwargs)
            value = func(*args, **kwargs)

            if deep_cpy_args != args:
                print("args has been modified")

            if deep_cpy_kwargs != kwargs:
                print("kwargs has been modified")

            print(f"{func.__name__!r} returned {value!r}")  # 4
            return value
        # print(argspecs)
        # for i in range(args_len):
        #     try
        #
        # input_log = f"Tracing {func.__name__}{function_args}. " \
        #             f"Called with following values: {func.__name__}, {args} -- {kwargs}"
        # if file is None:
        #     print(input_log)
        # output = func(*args, **kwargs)
        # return output
        return wrapper
    return inner_function


@trace(silent=True)
def hi(name, teemo, num = 20, crazy = ''):
    teemo = "captain teeto on duteeeee"
    crazy.append(5)
    print(f"Hi, {name}, {teemo},{num}, {crazy}")


if __name__ == "__main__":
    for i in range(10):
        hi("yee", "Captain teemo on duty", crazy=[1, 2, 3, 4])
