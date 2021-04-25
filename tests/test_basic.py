from src.yeezy.app import Yeezy
from typing import List
from functools import wraps

yee = Yeezy(__file__)


def test_initialization():
    """
    Test the initialization of the application
    """
    assert yee is not None


def test_class_side_effect_detection():
    """
    Unit test should detect side effect
    inside of method do_side_effect()
    :return:
    """
    class Test:
        def __init__(self, ass):
            self.yee = [1, 2, 3, 4, 5]

        def do_side_effect(self, a: List):
            a.append(10)


def test_extension():
    """
    Unit test extension case.
    Add a new decorator and test its performance
    :return:
    """
    class Yee(Yeezy):
        def __init__(self, name):
            super().__init__(name)

        def yee(self,
                passed_func: None):
            """
            Custom function should work properly
            """

            def inner_function(func):
                self._add_function(func, self.custom)

                @wraps(func)
                def wrapper(*args, **kwargs):
                    output = func(*args, **kwargs)
                    return output

                return wrapper

            # Make func callable
            if callable(passed_func):
                return inner_function(passed_func)

            return inner_function

    yeezy = Yee(__name__)

    @yeezy.yee
    def teemo(msg):
        print(msg)

    for i in range(10):
        teemo('yee')


def test_imported_func():
    """
    Test to see whether profiling imported function works well.
    """
    from dummy_package.util import long_func
    yee = Yeezy(__file__)

    # Wrap the imported function
    wrapped_long_func = yee.time(long_func)
    iteration_count = 10

    for i in range(iteration_count):
        wrapped_long_func()
    # run profile ... this should work
    yee.analyze()

    assert long_func in yee.time_dict, f"Cannot find function ... {long_func.__name__}"
    item = yee.time_dict[long_func]

    # If iteration count increased, this means
    # wrapped function is timing the function
    assert item['count'] == iteration_count


