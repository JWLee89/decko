from functools import wraps


def before_decorator_with_args(*decorated_func_args, **decorated_func_kwargs):
    def inner(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

