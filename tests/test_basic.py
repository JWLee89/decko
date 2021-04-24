from src.yeezy.app import Yeezy
from typing import List

yee = Yeezy(__file__)


def test_decorator_registration():
    print(yee)
    print(__name__)
    assert yee is not None


def test_class_side_effect_detection():
    class Test:
        def __init__(self, ass):
            self.yee = [1, 2, 3, 4, 5]

        def do_side_effect(self, a: List):
            a.append(10)


def test_imported_func():
    """
    Test to see whether profiling imported function works well
    :return:
    :rtype:
    """
    from dummy_package.util import long_func
    yee = Yeezy(__file__)

    # Wrap the imported function
    wrapped_long_func = yee.time(long_func)
    iteration_count = 10

    for i in range(iteration_count):
        wrapped_long_func()
    # run profile ... this should work
    yee.profile()

    assert long_func in yee.time_dict, f"Cannot find function ... {long_func.__name__}"
    item = yee.time_dict[long_func]

    # If iteration count increased, this means
    # wrapped function is timing the function
    assert item['count'] == iteration_count


