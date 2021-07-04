import logging
import inspect
import traceback
import typing as t
from time import process_time

# Local imports
from .decorators import deckorator


__FORMATTER__ = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

# -----------------------------------
# -------- Private Functions --------
# -----------------------------------


def _setup_logger(name: str,
                  log_file_path: str,
                  log_to_console: bool = True,
                  level=logging.INFO):
    """
    To setup as many loggers as you want

    Args:
        name (str): The name of the logger.
        log_file_path (str): The path where log will be stored
        log_to_console (bool): If set to true, log also to console
        level (int): The threshold level for logging

    Returns:
        A logger designed for handling logging.
        Ensures that only the necessary loggers are created
        for each module
    """
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(__FORMATTER__)

    logger = logging.getLogger(name)

    # Add file handler
    logger.setLevel(level)
    logger.addHandler(file_handler)

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(__FORMATTER__)
        logger.addHandler(console_handler)

    return logger


def _get_default_args(func: t.Callable) -> t.Dict:
    """
    Get the default arguments for a function
    Args:
        func: The function to retrieve default arguments for

    Returns:
        A dictionary containing the name of the argument
        and the default value assigned to the argument.
    """
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def _init_logger(decorator_function: t.Callable,
                 function_to_decorate: t.Callable,
                 file_path: str,
                 logging_level: int,
                 truncate_longer_than: int,
                 log_to_console: bool) -> t.Tuple[t.Dict, logging.Logger]:
    """
    Private function for initializing logger.
    Users may choose to override this when decorating a function

    Args:
        decorator_function: The decorator function applied
        function_to_decorate: The function that will be decorated.
        In the example below, this would be
        file_path: The path where logger will log output to
        logging_level: The logging level threshold for which to trigger event
        truncate_longer_than: Truncate arguments and outputs longer than specified
        log_to_console: Log to console if set to true
    Returns:
        A two-tuple containing
    """
    logger = _setup_logger(__name__, file_path, log_to_console, logging_level)
    default_args = _get_default_args(function_to_decorate)
    return default_args, logger


@deckorator(str,
            logging_level=(logging.INFO, int),
            truncate_longer_than=(100, int),
            log_to_console=(True, bool),
            on_decorator_creation=_init_logger,
            )
def log_trace(decorated_function,
              # From on_decorator_creation
              default_args: t.Dict,
              logger: logging.Logger,

              # Function arguments
              file_path: str,            # Specified arg template of type 'str'
              logging_level: int,        # Specified arg template of type 'int' with default: logging.INFO
              truncate_longer_than: int,
              log_to_console: bool,
              *args,
              **kwargs):
    """
    log_trace is a powerful function that does the following:

    1. Logs the function called plus the argument passed to a user-defined file
    2. Logs the output of that function
    3. Measures and logs the amount of time taken to execute that function

    Args:
        decorated_function (t.Callable): The function that is decorated with log_trace
        default_args (t.Dict): A dictionary containing default_argument name as keys
        and its corresponding default value
        logger (logger.Logger): The logger object used for logging
        file_path (str): the path with file is stored
        logging_level (int):
        truncate_longer_than (int):
        *args:
        **kwargs:

    Returns:

    """
    func_name = decorated_function.__name__
    args_to_log = list(args)

    # Handle kwargs
    for key in default_args.keys():
        if key in kwargs:
            args_to_log.append(kwargs[key])
        else:
            args_to_log.append(default_args[key])

    # Create argument string
    args_to_log = ", ".join(str(argument) for argument in args_to_log)[:truncate_longer_than]

    # Measure execution time
    start_time = process_time()
    output = decorated_function(*args, **kwargs)
    time_elapsed = process_time() - start_time

    # Create output to log
    try:
        output_to_log = output[:truncate_longer_than]
    except Exception:
        output_to_log = output
    # Log outputs
    logger.log(logging_level,
               f"{func_name}({args_to_log}) -> {output_to_log}, '{time_elapsed * 1000} milliseconds'")
    return output


@deckorator(t.Tuple, t.Callable, raise_error=(False, bool))
def try_except(decorated_function: t.Callable,
               errors_to_catch: t.Tuple[Exception],
               error_callback: t.Callable,
               raise_error: bool = False,
               *args, **kwargs):
    """
    Wraps the entire function around a try-catch block and
    catches the exception.
    Args:
        decorated_function: The function that was wrapped
        errors_to_catch: A tuple of exceptions to catch
        error_callback: The error callback to call when exception is caught
        raise_error: If set to true, after handling error_callback, an error will
        be raised.
    Returns:
        A decorator that handles errors.
    """
    try:
        return decorated_function(*args, **kwargs)
    except errors_to_catch as error:
        tb = traceback.format_exc()
        error_callback(error, tb)
        if raise_error:
            raise


@deckorator(t.Callable)
def stopwatch(decorated_function: t.Callable,
              callback: t.Callable,
              *args,
              **kwargs):
    """
    A stopwatch function that measures the amount of time
    taken to execute a function.
    Args:
        decorated_function: The decorated function
        callback: A callback function that is executed to handle
        the calculation of the amount of time taken to execute
        decorated function.
        Defaults to print.
    Returns:
        A callable object that executes decorated function
        but with the additional feature of processing the amount of
        time taken to execute function.
    """
    start_time = process_time()
    output = decorated_function(*args, **kwargs)
    time_elapsed = process_time() - start_time
    callback(time_elapsed)
    return output
