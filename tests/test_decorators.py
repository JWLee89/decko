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


def test_instance_data():
    def setter(self, new_val):
        if new_val > 20:
            raise ValueError("Value set is greater than 20 ... ")

    @fd.instance_data(setter=setter)
    class ClassSample:
        class_var_data = 3

        def __init__(self, a, b):
            self.a = a
            self.b = b

        def __repr__(self):
            return f"a:{self.a}, b: {self.b}"

    class_sample = ClassSample(1, 2)

    with pytest.raises(ValueError) as err:
        class_sample.a = 22


def test_filter_by_output():
    @fd.filter_by_output(lambda x: x > 2)
    def get_number(x):
        return x

    output = []
    iter_count = 5
    for i in range(iter_count):
        output.append(get_number(i))

    assert output == [None, None, None, 3, 4], \
        "Hmmm ... weird"


@pytest.mark.parametrize("inputs", [
    (40, 30),
    (20, 10),
    (15, 25)  # does not exceed size limit
])
def test_truncate(inputs):
    size, size_limit = inputs

    @fd.truncate(size_limit)
    def double(numbers, sliceable):
        return sliceable(num * 2 for num in numbers)

    a_list = list(range(size))
    truncated_doubled_list = double(a_list, list)
    truncated_doubled_tuple = double(a_list, tuple)

    if size_limit > size:
        target_size = size
    else:
        target_size = size_limit
    msg = f"List should have {target_size} elements"

    # Should be the same after size limit
    assert len(truncated_doubled_list) == target_size \
           and isinstance(truncated_doubled_list, list), msg
    assert len(truncated_doubled_tuple) == target_size \
           and isinstance(truncated_doubled_tuple, tuple), msg

    # Should also work for strings
    @fd.truncate(size_limit)
    def repeat_str(msg, count):
        return msg * count

    repeated_str = repeat_str("badger", size)
    assert len(repeated_str) == size_limit, msg

    # should not work for invalid types
    @fd.truncate(size_limit)
    def should_not_work(num):
        return num * 200

    with pytest.raises(TypeError) as err:
        num = should_not_work(size)


def test_singleton():
    @fd.singleton()
    class ShouldBeSingleton:
        def __init__(self):
            self.a = 1

    first_obj = ShouldBeSingleton()
    second_obj = ShouldBeSingleton()
    first_obj.a = 2

    assert first_obj is second_obj, "singletons should point to same object"
    assert first_obj.a == second_obj.a, "Change in first_obj should be reflected in second_obj"
