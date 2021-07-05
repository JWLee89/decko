import typing as t
from .decorators import deckorator


@deckorator((t.Tuple, t.List))
def validate_inputs(decorated_function: t.Callable,
                    validation_functions: t.Union[t.Tuple, t.List],
                    *args,
                    **kwargs):
    """
    Given a list of functions, validate the inputs and raise
    an error if the inputs don't pass sanity check
    Args:
        decorated_function: The decorated function
        validation_functions: A list or tuple of validation function to run on inputs.
        By default, a one-to-one matching is performed.
        However, if there are three arguments and only one validation function is
        provided, the validation function will receive all three inputs.
    Returns:
        A decorator that validates inputs
    """
    kwarg_values: t.List = kwargs.values()
    inputs = args + kwarg_values if kwarg_values else args
    i = 0
    for is_valid in validation_functions:
        if not is_valid(inputs[i]):
            raise ValueError(f"Invalid inputs: {inputs[i]}")

    return decorated_function(*args, **kwargs)
