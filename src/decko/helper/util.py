import copy
import typing as t
from functools import wraps
import inspect
import logging

from .validation import check_instance_of


def create_instance(cls: t.Any, *args):
    """
    Create an instance of a new class dynamically using random arguments.
    Note: This creation will be difficult for classes
    that perform validation in the instantiation phase.
    :param cls: The class to instantiate
    :return: An instance of Class <cls>
    """
    # for inspection purposes
    class NewClass(cls):
        pass

    # Get the number of arguments to create a dummy instance of a class
    # Used for decorating a class
    arg_count = len(inspect.getfullargspec(NewClass.__init__).args) - 1
    # Use placeholder values to initialize
    if arg_count > len(args):
        new_args = tuple(args) + tuple(range(arg_count - len(args)))
        instance = NewClass(*new_args)
    else:
        instance = NewClass(*args)
    return instance


def get_deepcopy_args_kwargs(fn: t.Callable, args: t.Tuple, kwargs: t.Dict):
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
    for k, v in parameters.items():
        if i >= arg_count:
            new_args[k] = v.default
        i += 1
    return copy.deepcopy(args), copy.deepcopy(kwargs)


def fill_default_kwargs(fn: t.Callable, args: t.Tuple, kwargs: t.Dict):
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


def get_shallow_default_arg_dict(fn: t.Callable, args: t.Tuple):
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
    arg_count = len(args)
    args_names = []
    # Add defaults
    parameters = inspect.signature(fn).parameters
    new_kwargs = {}
    i: int = 1
    for k, v in parameters.items():
        if i > arg_count:
            new_kwargs[k] = v.default
        else:
            args_names.append(k)
        i += 1
    return {**dict(zip(args_names, args)), **new_kwargs}


def create_properties(valid_properties: t.Dict, **kwargs) -> t.Dict:
    """
    Add properties from kwargs to valid_properties
    :param valid_properties: A dictionary containing valid properties
    :param kwargs:
    """
    properties: t.Dict = {}
    # Validate and add properties
    for key, (data_type, default_value) in valid_properties.items():
        if key in kwargs:
            current_property = kwargs[key]
            if isinstance(current_property, t.Tuple):
                for item in current_property:
                    check_instance_of(item, data_type)
            else:
                check_instance_of(current_property, data_type)
            properties[key] = kwargs[key]
        else:
            properties[key] = default_value
    return properties


def get_unique_func_name(func: t.Callable) -> str:
    return f'{func.__module__}.{func.__qualname__}'


def dict_is_empty(obj: t.Dict):
    if not isinstance(obj, t.Dict):
        raise TypeError("Object is not a dictionary. "
                        f"Passed in type: {type(obj)}")
    for _ in obj.keys():
        return False
    return True


class LoggingLevelError(ValueError):
    """
    Occurs if users pass in an invalid logging type
    to logging function
    """
    def __init__(self, msg):
        super().__init__(msg)


def logger_factory(logger_name: str,
                   level: int = logging.DEBUG,
                   file_name: str = None) -> t.Callable:
    """
    Function for writing information to a file during program execution
    :param file_name: The name of the file to store log
    :param logger_name: The name of the function being called
    :param level: The debug level
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

    def log_msg(contents_to_log: t.Union[str, t.List],
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
    def __call__(self, func: t.Callable) -> t.Callable:
        self.wrapped_func = func

        @wraps(func)
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return inner


def truncate(max_length: int) -> t.Callable:
    """
    Responsible for truncating a sentence based on its length
    :param max_length:
    :return: a truncation function
    """
    def do_truncate(sentence: str) -> str:
        truncated_sentence = (sentence[:max_length], ' ...') if len(sentence) > max_length else sentence
        return truncated_sentence
    return do_truncate


class TraceDecorator:
    def __init__(self, func: t.Callable, verbose: bool = False):
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


def attach_property(cls: t.Any,
                    prop: str,
                    getter = None,
                    setter = None):
    accessor: str = f"_{cls.__name__}__{prop}"

    def create_getter(func):

        @wraps(func)
        def executor(self):
            func(self)
            return getattr(self, accessor)
        return executor

    def create_setter(func):

        @wraps(func)
        def executor(self, value):
            func(self, value)
            setattr(self, accessor, value)

        return executor

    # Create property dynamically
    # By default, they are the same

    if getter is None:
        def getter(self):
            return getattr(self, accessor)
    if setter is None:
        def setter(self, v):
            setattr(self, accessor, v)

    test = property(create_getter(getter))
    test = test.setter(create_setter(setter))
    setattr(cls, prop, test)


def format_list_str(list_of_stuff: t.Union[t.List, t.Tuple]):
    return ',\n'.join(list_of_stuff)
