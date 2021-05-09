# Pojang

A decorator based utility module for Python developers. The module is designed to 
aid developers in debugging their python applications.

![yee.png](yee.png)

## Getting Started

Pojang is a decorated-based module for debugging. 
It also provides useful decorators to speed up programming and provides utility 
function for easier decorator usage. Here is an example

```python
from pojang import Pojang

pj = Pojang(__name__, debug=True)


@pj.stopwatch
def create_list(n=1000000):
    return list(range(n))


# Returns statistics on time
pj.analyze()
```

### Features

Pojang detects and raises customized, informative errors such as `DuplicateDecoratorError`.
This helps in debugging and extending features with minimal modifications to the existing
codebase.

```python
from src.pojang import Pojang

pj = Pojang(__name__, debug=True)


def log_impurity(argument, before, after):
    print(f"Argument: {argument} modified. Before: {before}, after: {after}")

def i_run_before(a, b, c, item):
    print(f"Run before func: {a}, {b}, {c}, {item}")

@pj.run_before(i_run_before)
@pj.run_before(i_run_before)     # This should not be allowed
@pj.pure(log_impurity)
# @pj.profile
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

    # @pj.pure(log_impurity)
    # @pj.profile
    def set_item(self, item):
        self.item = item

    def __repr__(self):
        return f'DummyClass: {self.item}'


test = DummyClass(10)
test.set_item(20)

# Error raised
output = expensive_func(10, 20, 40)
```


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
src.pojang.exceptions.DuplicateDecoratorError: Found duplicate decorator with identity: __main__.expensive_func
```


