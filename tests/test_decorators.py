import pytest
import typing as t

import src.decko.decorators as fd
from src.decko import decorators


@pytest.mark.parametrize("iter_count", [
    10, 50, 7
])
def test_deckorator(iter_count):
    """
    Basic decoration test
    """

    counter_dict = {'counter': 0}

    @fd.deckorator(t.Dict)
    def new_decorator(decorated_func,
                      passed_in_counter_dict,
                      *args,
                      **kwargs):
        output = decorated_func(*args, **kwargs)
        passed_in_counter_dict['counter'] += 1
        return output

    @new_decorator(counter_dict)
    def get_int(i):
        return i

    for i in range(iter_count):
        get_int(i)

    assert counter_dict['counter'] == iter_count, "Decorator not working as intended ..."


@pytest.mark.parametrize("data_types", [
    (int, float),
    (int, str, t.Callable),
])
@pytest.mark.parametrize("decorator_args", [
    (1, print),     # print is a callable, not a float
    (1, "here"),    # Missing required argument: callable
])
def test_check_for_invalid_data_types(data_types, decorator_args):
    """
    Type check safety should work and raise Errors since
    passed in arguments do not match the specified data types
    """

    @fd.deckorator(*data_types)
    def a_decorator(wrapped_function,
                    *args,
                    **kwargs):
        return wrapped_function(*args, **kwargs)

    with pytest.raises((ValueError, TypeError)):
        @a_decorator(*decorator_args)
        def decorate_me(num):
            return num


def test_check_valid_data_types():
    """
    Since we passed in the right data types here,
    there should be no exception when running or instantiating
    the function
    """
    data_types = [
        (int, t.Callable),
        (int, str, t.Callable),
        ((int, float), str),    # passes if input is either a float or int
    ]

    decorator_args = [
        (1, print),             # print is a callable, not a float
        (1, "here", print),     # Missing required argument: callable
        (1.0, "here"),
    ]

    assert len(data_types) == len(decorator_args), "Invalid unit test. Check input sizes"

    for i, (data_type, decorator_arguments) in enumerate(zip(data_types, decorator_args)):

        @fd.deckorator(*data_type)
        def a_decorator(wrapped_function,
                        *args,
                        **kwargs):
            print(f"args: {args}")
            decorate_me_input = args[len(data_types[i])]
            return wrapped_function(decorate_me_input, **kwargs)

        # Should
        @a_decorator(*decorator_arguments)
        def decorate_me(num):
            return num

        decorate_me(100)


def test_decorator_kwarg():

    arg_one = 20

    @fd.deckorator((float, int), kwarg_val=10)
    def a_decorator(wrapped_function,
                    arg_1,
                    kwarg_val,
                    *args,
                    **kwargs):
        assert kwarg_val == 10 and arg_1 == arg_one
        return wrapped_function(*args, **kwargs)

    @a_decorator(arg_one)
    def test(new_num):
        return new_num

    test(15)


@pytest.mark.parametrize("invalid_inputs", [
    10, 200.0, "string is also invalid"
])
def test_invalid_decorator_kwarg(invalid_inputs):

    # This should raise an error, since default arg 10 is not Callable
    @fd.deckorator(kwarg_val=(10, t.Callable))
    def error_decorator(wrapped_function,
                    kwarg_val,
                    *args,
                    **kwargs):
        return wrapped_function(*args, **kwargs)

    with pytest.raises(TypeError):
        @error_decorator()
        def test(new_num):
            return new_num

    with pytest.raises(TypeError):
        @error_decorator(invalid_inputs)
        def test(new_num):
            return new_num


@pytest.mark.parametrize("valid_input", [
    10, 200.0, "a string"
])
def test_override_decorator_kwarg_val(valid_input):

    # This should raise an error, since default arg 10 is not Callable
    @fd.deckorator(kwarg_val=(10, int, float, str))
    def valid_decorator(wrapped_function,
                    kwarg_val,
                    *args,
                    **kwargs):
        assert kwarg_val == valid_input, "This value should be overriden ..."
        return wrapped_function(*args, **kwargs)

    # Override default values
    @valid_decorator(valid_input)
    def test(new_num):
        return new_num

    test(10)


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


@pytest.mark.parametrize("input_data",
                         [
                             (10000000, 50),
                             (20000000, 100),
                             (30000000, 150),
                         ])
def test_slower_than(input_data):
    input_size, milliseconds = input_data

    def raise_error(time_elapsed, threshold_time):
        raise ValueError(f"Took {time_elapsed} milliseconds. "
                         f"Should take less than {threshold_time}")

    @decorators.slower_than(milliseconds, raise_error)
    def long_func(n):
        x = 0
        for i in range(n):
            x += i
        return x

    # Ideally these functions should take some time to complete
    with pytest.raises(ValueError):
        long_func(input_size)


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
    """
    Singleton classes should point to the same object.
    TODO: Test later with race conditions
    """

    @fd.singleton()
    class ShouldBeSingleton:
        def __init__(self):
            self.a = 1

    first_obj = ShouldBeSingleton()
    second_obj = ShouldBeSingleton()
    first_obj.a = 2

    assert first_obj is second_obj, "singletons should point to same object"
    assert first_obj.a == second_obj.a, "Change in first_obj should be reflected in second_obj"


@pytest.mark.parametrize("default_args", [
    {'test_default': (bool, True), 'numeric': (int, 10)},
])
@pytest.mark.parametrize("user_defined_args", [
    {'test_default': True}
])
@pytest.mark.parametrize('expected', [
    {'test_default': True, 'numeric': 10}
])
def test_set_defaults_if_not_defined(default_args,
                                     user_defined_args,
                                     expected):
    fd._set_defaults_if_not_defined(user_defined_args, default_args)

    for prop_name, value in user_defined_args.items():
        # The property should exist in both the expected and default dictionary
        assert prop_name in expected, f"Missing expected property: {prop_name}"
        assert prop_name in default_args, f"Missing expected property: {prop_name} " \
                                          "in default_args dictionary"
        # Value should be expected type
        expected_type = default_args[prop_name][0]
        assert isinstance(value, expected_type), \
            f"Expected type: '{expected_type}', got '{type(value)}'"
