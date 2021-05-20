import pytest
import src.decko.decorators as fd


@pytest.mark.parametrize("iter_count", [
    4, 8, 12
])
def test_stopwatch(iter_count):
    time_elapsed_arr = []

    def callback(val):
        time_elapsed_arr.append(val)
        return val

    @fd.stopwatch(callback)
    def create_list(n):
        return list(range(n))

    for i in range(iter_count):
        create_list(1000000 * i)

    assert len(time_elapsed_arr) == iter_count, \
        f"Should have {len(time_elapsed_arr)} items"


def test_class_freeze():
    @fd.freeze
    class RandomClass:
        def __init__(self, a_tuple):
            self.a_tuple = a_tuple

    cls_instance = RandomClass((1, 2, 3))

    # Frozen class should not be able to mutate existing properties
    with pytest.raises(Exception):
        cls_instance.a_tuple = 100

    # Or add new ones
    with pytest.raises(Exception):
        cls_instance.new_prop = 100

    # Decorating a function with freeze should raise an error
    with pytest.raises(Exception):
        @fd.freeze
        def random_func(test):
            print(f"Test random_func: {test}")

