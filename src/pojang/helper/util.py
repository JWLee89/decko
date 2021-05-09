import copy
import time
from typing import List, Callable, Union, Dict, Tuple, Type
from functools import wraps
import inspect
import logging


def is_iterable(obj) -> bool:
    iterable = True
    try:
        iter(obj)
    except TypeError:
        iterable = False
    return iterable


def validate_type(value, target_type: Type):
    if type(value) != target_type:
        raise TypeError(f"{value} must be of type boolean. "
                        f"{value} is of type: {type(value)}")


def get_deepcopy_args_kwargs(fn: Callable, args: Tuple, kwargs: Dict):
    """
    Return deep copies of arg_kwargs with default values included
    :param fn: The target function to evaluate
    :param args:
    :param kwargs:
    :return: Dict of key value pairs
    """
    # Add defaults
    parameters = inspect.signature(fn).parameters
    arg_count: int = len(args)
    new_args = {}
    i: int = 0
    print(parameters.values())
    for k, v in parameters.items():
        print(f"key: {k}, {v}")
        if i >= arg_count:
            new_args[k] = v.default
        i += 1
    return copy.deepcopy(args), copy.deepcopy(kwargs)


def fill_default_kwargs(fn: Callable, args: Tuple, kwargs: Dict):
    """
    Kwarg is empty if default values are used during runtime.
    Fill the kwargs with default values
    """
    parameters = inspect.signature(fn).parameters
    arg_count: int = len(args)
    i: int = 0
    for k, v in parameters.items():
        if i >= arg_count:
            kwargs[k] = v.default
        i += 1


def get_shallow_default_arg_dict(fn: Callable, args: Tuple):
    """
    Return key value pair comprised of
        key: The name of the variable
        value: The value passed
    :param fn: The target function to evaluate
    :param args:
    :param kwargs:
    :return: Dict of key value pairs
    """
    # Add defaults
    code = fn.__code__
    arg_count = len(args)
    args_names = code.co_varnames[:arg_count]
    # Add defaults
    parameters = inspect.signature(fn).parameters
    new_kwargs = {}

    i: int = 0
    for k, v in parameters.items():
        if i >= arg_count:
            print(v)
            new_kwargs[k] = v.default
        i += 1

    return {**dict(zip(args_names, args)), **new_kwargs}


def create_properties(valid_properties: Dict, **kwargs) -> Dict:
    """
    Add properties from kwargs to valid_properties
    :param valid_properties: A dictionary containing valid properties
    :param kwargs:
    """
    properties: Dict = {}
    # Validate and add properties
    for key, (data_type, default_value) in valid_properties.items():
        if key in kwargs:
            current_property = kwargs[key]
            if isinstance(current_property, Tuple):
                for item in current_property:
                    validate_type(item, data_type)
            else:
                validate_type(current_property, data_type)
            properties[key] = kwargs[key]
        else:
            properties[key] = default_value
    return properties


def is_class_instance(item) -> bool:
    """
    Check if item is a class instance.
    :param item: The item to evaluate
    """
    # return hasattr(item, '__dict__')
    return inspect.isclass(item)


def get_unique_func_name(func: Callable) -> str:
    return f'{func.__module__}.{func.__qualname__}'


def dict_is_empty(dictionary: Dict):
    for _ in dictionary.keys():
        return True
    return False


class LoggingLevelError(ValueError):
    """
    Occurs if users pass in an invalid logging type
    to logging function
    """
    def __init__(self, msg):
        super().__init__(msg)


def logger_factory(logger_name: str,
                   level: int = logging.DEBUG,
                   file_name: str = None,
                   log_also_to_console: bool = True) -> Callable:
    """
    Function for writing information to a file during program execution
    :param file_name: The name of the file to store log
    :param logger_name: The name of the function being called
    :param level: The debug level
    :param log_also_to_console: If set to true, logging will be
    performed both to the file and the console
    """
    # This is required for logging rules to apply
    logging.basicConfig(level=level)

    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                  '%Y-%m-%d %H:%M:%S')

    # remove all old handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # add file logging
    if file_name is not None:
        file_handler = logging.FileHandler(file_name, 'a')

        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        # set the new handler
        logger.addHandler(file_handler)

    # Add console handler with same formatter
    if log_also_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    def log_msg(contents_to_log: Union[str, List],
                log_level: int = logging.DEBUG) -> None:
        """
        When utilizing this function, please note that file I/O is relatively costly,
        so try calling this function at the end of creating a message string
        :param contents_to_log: The contents to append to the target log file.
        :param log_level: The log level specified by the python logging module
        which are as follows:

            Level	Numeric value
            CRITICAL	50
            ERROR	    40
            WARNING	    30
            INFO	    20
            DEBUG	    10
            NOTSET	    0

        """
        # Log levels will likely not be added in the future
        if logging.INFO == log_level:
            log_to_file = logger.info
        elif logging.DEBUG == log_level:
            log_to_file = logger.debug
        elif logging.WARNING == log_level:
            log_to_file = logger.warning
        elif logging.ERROR == log_level:
            log_to_file = logger.error
        elif logging.CRITICAL == log_level:
            log_to_file = logger.critical
        else:
            raise LoggingLevelError("Invalid log level passed to log_msg(contents_to_log, log_level): "
                                    f"log_level={log_level} is invalid.")
        log_to_file(contents_to_log)

    return log_msg


class ContextDecorator:
    """
    Used for creating decorators that behave both
    as decorators and context managers
    """
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


def compute_stats(computation_function):
    def inner_func(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            output = fn(*args, **kwargs)
            computation_function(output, *args, **kwargs)
            return output
        return wrapper
    return inner_func
