import time
import functools
from typing import List, Callable
import inspect


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

    def __call__(self, *args, **kwargs):
        ...
        # use self.param1
        result = self.func(*args, **kwargs)
        # use self.param2
        return result


def trace(verbose=None):

    def inner_function(func):

        # Get arguments
        argspecs = inspect.getfullargspec(func)
        function_args = inspect.signature(func)
        args_len = len(argspecs.args)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args_repr = [repr(a) for a in args]  # 1
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
            signature = ", ".join(args_repr + kwargs_repr)  # 3
            if verbose:
                input_log = f"Tracing {func.__name__}{function_args}. " \
                            f"Called with following values: {func.__name__}, {args} -- {kwargs}"
                print(input_log)
                print(argspecs)

            print(f"Calling {func.__name__}({signature})")
            value = func(*args, **kwargs)
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


@trace(verbose=True)
def hi(name, teemo, num = 20, crazy = ''):
    print(f"Hi, {name}, {teemo},{num}, {crazy}")


if __name__ == "__main__":
    hi("yee", "Captain teemo on duty", crazy=13333)
