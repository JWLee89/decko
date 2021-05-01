import copy
import time
import functools
from typing import List, Callable, Union
from functools import wraps
import inspect
import logging

# Handle fallback in case ContextDecorator does not work
# try:
#     from contextlib import ContextDecorator
# except ImportError:
#     version_info = sys.version_info
#     python_version = f'{version_info.major}.{version_info.minor}.{version_info.micro}-' \
#                      f'{version_info.releaselevel}'
#
#     # TODO: Change this message later
#     print('cannot import contextmanager from contextlib. '
#           f'Current python version: {python_version}. Requires version >= 3.2.\n'
#           f'Attempting to create fallback method ...')


def is_class_instance(item):
    return hasattr(item, '__dict__')


def flexible_decorator(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def create_before_decorator(*args_outer, **kwargs_outer):
    """
    Simple utility function for creating before decorators.

    Before decorators are decorators that perform c

    :param func_to_decorate: The function to decorate
    :param exec_before_func: The function to execute before decorated function
    :return:
    :rtype:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            output = func(*args, **kwargs)
            return output

        return wrapper

    return decorator


class ContextDecorator:
    def __call__(self, func: Callable) -> Callable:
        self.wrapped_func = func

        @wraps(func)
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return inner


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


class ClassDecorator(ContextDecorator):
    pass


class TimeComputer(ContextDecorator):
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
        NS = 'nanoseconds'

    def __init__(self,
                 accumulated_time: Union[None, List] = None,
                 log_interval: int = 1,
                 log_callback: Callable = print) -> None:
        self._accumulated_time = accumulated_time
        self.log_interval = log_interval
        self.log_callback = log_callback

        # Determines how to handle computation
        # based on accumulated_time input
        # since list and floats are computed differently
        self._handle_computation = None

        self.run_count = 0
        self._init()

    def __enter__(self) -> None:
        self.run_count += 1
        self.start_time = time.time()

    def _init(self) -> None:
        self._validate()
        if isinstance(self._accumulated_time, list):
            self._handle_computation = self._append_to_list
        else:
            self._accumulated_time = 0
            self._handle_computation = self._compute_int

    def _compute_int(self, time_elapsed: float) -> None:
        self._accumulated_time += time_elapsed

    def _append_to_list(self, time_elapsed: float) -> None:
        self._accumulated_time.append(time_elapsed)

    def _validate(self):
        if not isinstance(self._accumulated_time, list) and self._accumulated_time is not None:
            # Case: passed in decorator as follows: @TimeComputer
            if isinstance(self._accumulated_time, Callable):
                self._accumulated_time = 0
            else:
                raise TypeError(f"Accumulated_time must be a list or None. "
                                f"Passed in type: {type(self._accumulated_time)}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        time_elapsed = time.time() - self.start_time
        self._handle_computation(time_elapsed)
        if self.run_count % self.log_interval == 0:
            self.log_callback(self._accumulated_time, self.run_count)

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


def check_key_values(orig_items, item_copy):
    for key in orig_items:
        key, original, after = key, 
        print(f"key: {key}, val: {orig_items[key]}, orig: {item_copy[key]}")
