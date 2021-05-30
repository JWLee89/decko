# Decko

A decorator based utility module for Python developers. The module is designed to 
aid developers in debugging their python applications.

Decko is not dependent on any external libraries that are not included in the standard Python package.
However, one may choose to extend with external libraries such as numba to improve its performance. 

Decko is meant to a utility to help people debug and extend code. Its original use case is not in
mission-critical fields where performance is key. 
If there is enough demand, I will create a separate branch which optimizes the runtime performance
of all decko functions.

## Updates / News 

Self-contained decorators that can be used without creating a `Decko` instance is under development.

## Install

Install and update using [pip](https://pypi.org/project/pip/):

```shell
pip install -U decko
```

## Uninstall 

Uninstall using pip:

```shell
pip uninstall decko
```

## Example

Decko is a decorated-based module for debugging. 
It also provides useful decorators to speed up programming and provides utility 
function for easier decorator usage. Here is an example

```python
from decko import Decko

if __name__ == "__main__":

    dk = Decko(__name__)

    def print_list_size(size, **kwargs):
        print(f"Size of list is: {size}")

    def print_kwargs(*args, **kwargs):
        print(f"args: {args}, kwargs: {kwargs}")

    @dk.run_before([print_list_size, print_kwargs])
    @dk.profile
    def create_list(n):
        return list(range(n))

    for i in range(20):
        create_list(100000)

    # print profiled result
    dk.print_profile()

    # event triggered when original input is modified
    def catch_input_modification(arg_name, before, after):
        print(f"The argument: {arg_name} has been modified.\n"
              f"Before: {before} \n After: {after}")
        print("-" * 200)

    @dk.pure(callback=catch_input_modification)
    def create_list(n,
                    item=[]):
        item.append(n)
        return list(range(n))


    # Raise error
    for i in range(20):
        create_list(100000)
```

Decko also provides standalone decorators that can be applied immediately to your projects. 
It also has built-in decorator functions to help developers quickly build debuggable custom 
decorators. This allows developers to modify and extend code with minimal modifications to 
the existing codebase.

`decorator` creates function decorators that can be used to decorate both functions and
classes. Demo for creating class and function decorators is shown below.

```python
from decko import decorators.deckorator as deckorator
import time
import typing as t


def timer(func):
    """
    An ordinary decorator.
    Will be used to check the
    performance of decorate function
    """

    def inner(*args, **kwargs):
        start_time = time.time()
        output = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"Time elapsed: {elapsed}")
        return output

    return inner

# Create decorator called "time_it" that accepts the following args
# 1. Int value
# 2. A callable object or a List
@deckorator((int, float), (t.Callable, t.List))
def time_it(wrapped_function,
            interval,
            callback,
            *args, **kwargs):
    print(f"wrapped function: {wrapped_function.__name__}, interval: {interval},"
          f" args: {args}")
    # Check every 5 interval
    i = time_it.called
    if (i + 1) % interval == 0:
        start_time = time.time()
        output = wrapped_function(*args, **kwargs)
        elapsed = time.time() - start_time
        callback(elapsed, i + 1)
    else:
        output = wrapped_function(*args, **kwargs)
    time_it.called += 1
    return output


time_it.called = 0


@deckorator
def immutable(wrapped_class,
              *args,
              **kwargs):

    def do_freeze(slf, name, value):
        msg = f"Class {type(slf)} is immutable. " \
              f"Attempted to set attribute '{name}' to value: '{value}'"
        raise AttributeError(msg)

    class Immutable(wrapped_class):
        """
        A basic immutable class
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            setattr(Immutable, '__setattr__', do_freeze)

    return Immutable(*args, **kwargs)


@immutable
class SampleClass:
    def __init__(self, a, teemo):
        self.a = a

    @time_it(1, print)
    @classmethod
    def method(cls):
        return "yee"


if __name__ == "__main__":
    # for i in range(10):
    #     long_list(10000000, i)

    deco_cls = SampleClass(10, 20)
    deco_cls.method()
    test = SampleClass(20, 40)
    try:
        deco_cls.a = 50
    except AttributeError:
        print("class is immutable")
    print(deco_cls.a)
```


### Features

Decko detects and raises customized, informative errors such as `DuplicateDecoratorError`.
This helps in debugging and extending features with minimal modifications to the existing
codebase.

```python
from decko import Decko

dk = Decko(__name__, debug=True)


def log_impurity(argument, before, after):
    print(f"Argument: {argument} modified. Before: {before}, after: {after}")


def i_run_before(a, b, c, item):
    print(f"Run before func: {a}, {b}, {c}, {item}")


@dk.run_before(i_run_before)    # This should not be allowed since it is a duplicate
@dk.run_before(i_run_before)  
@dk.pure(callback=log_impurity)
@dk.profile
def expensive_func(a,
                   b,
                   c=1000000,
                   item=[]):
    for i in range(100):
        temp_list = list(range(c))
        item.append(temp_list)

    a += 20
    b += a
    total = a + b
    return total


class DummyClass:
    def __init__(self, item):
        self.item = item

    # @dk.pure(log_impurity)
    # @dk.profile
    def set_item(self, item):
        self.item = item

    def __repr__(self):
        return f'DummyClass: {self.item}'


test = DummyClass(10)
test.set_item(20)

# Error raised
output = expensive_func(10, 20, 40)
```

Decko raises informative error messages to help debug issues.
In later versions, features to define error callbacks with custom exceptions will be made.

```shell
Traceback (most recent call last):
  File "path", line 17, in <module>
    def expensive_func(a,
  File "path", line 522, in wrapper
    fn: t.Callable = self._decorate(self.run_before, fn)
  File "path", line 334, in _decorate
    self.add_decorator_rule(decorator_func, func)
  File "path", line 241, in add_decorator_rule
    self._add_function_decorator_rule(decorator_func,
  File "path", line 213, in _add_function_decorator_rule
    self._update_decoration_info(decorator_func, func, properties)
  File "path", line 490, in _update_decoration_info
    self.handle_error(f"Found duplicate decorator with identity: {func_name}",
  File "path", line 325, in handle_error
    raise error_type(msg)
src.decko.exceptions.DuplicateDecoratorError: Found duplicate decorator with identity: __main__.expensive_func
```

## Links

- Documentation (work in progress): [https://github.com/JWLee89/decko/wiki]()
- PyPI Releases: [https://github.com/JWLee89/decko]()
- Source Code: [https://github.com/pallets/flask/]()

