# Decko

A decorator based utility module for Python developers. The module is designed to 
aid developers in debugging their python applications.

## Getting Started

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

    @dk.pure(catch_input_modification)
    def create_list(n,
                    item=[]):
        item.append(n)
        return list(range(n))


    # Raise error
    for i in range(20):
        create_list(100000)
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
@dk.pure(log_impurity)
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
    fn: Callable = self._decorate(self.run_before, fn)
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


