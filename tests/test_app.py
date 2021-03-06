import os
import pytest
from typing import Iterable, List
from tests.common.fixtures import decko_fixture
from src.decko.helper.exceptions import ImmutableError


def get_src_python_files(root_folder: str, exclude: Iterable):
    src_files = []
    for subdir, dirs, files in os.walk(root_folder):
        for file in files:
            filepath = subdir + os.sep + file
            filepath = filepath.replace(root_folder, "")
            if filepath.endswith(".py") and \
                    file != "__init__.py" and file not in exclude:
                src_files.append(filepath)
    return src_files


def get_test_python_files(root_folder: str):
    src_files: List = []
    for subdir, dirs, files in os.walk(root_folder):
        for file in files:
            file = file.replace("test_", "")
            filepath = subdir + os.sep + file
            filepath = filepath.replace(root_folder, "")
            if filepath.endswith(".py") and file != "__init__.py":
                src_files.append(filepath)
    return src_files


# -----------------------------------------
# ------------ Begin Unit Test ------------
# -----------------------------------------

# def test_unit_test_count():
#     """
#     Test and ensure that unit test exists for each file.
#     """
#
#     # Paths
#     test_path = f"{ROOT_DIR}/tests"
#     src_path = f"{ROOT_DIR}/src/decko"
#
#     # src folder must obviously exist
#     src_exists = os.path.exists(src_path)
#     assert src_exists, f"source folder does not exist in path: {src_path}"
#     assert test_path, f"test folder does not exist in path: {test_path}"
#
#     # Grab all the file names from src and test directory
#     src_files = sorted(get_src_python_files(src_path, exclude=TESTS_TO_EXCLUDE))
#     test_files = sorted(get_test_python_files(test_path))
#     missing_unit_tests = []
#     # Now, logger each missing test file
#     i, j = 0, 0
#     while i < len(src_files) and j < len(test_files):
#         src_file, test_file = src_files[i], test_files[j]
#         if src_file == test_file:
#             i += 1
#             j += 1
#         else:
#             missing_unit_tests.append(src_file)
#             i += 1
#
#     # There should be a corresponding unit test for each python file
#     assert len(missing_unit_tests) == 0, \
#         f"Missing {len(missing_unit_tests)} unit test for the " \
#         f"following files:\n{format_list_str(missing_unit_tests)}.\n" \
#     f"Corresponding files: {src_files}, {test_files}"


"""
    Unit test:

        1. Property name: debug
        E.g. self.debug
"""


def test_set_debug(decko_fixture) -> None:
    """
    This should not trigger a type error, since we are
    setting debug to a boolean value
    """
    try:
        decko_fixture.debug = True
        decko_fixture.debug = False
    except TypeError:
        pytest.fail("This should not occur since .debug must "
                    "be set to boolean value.")
    assert not decko_fixture.debug, f"Expected: 'False', actual: {decko_fixture.debug}"


def test_invalid_set_debug(decko_fixture) -> None:
    """
    This should trigger a type error, since we are
    setting debug to a string value
    """
    with pytest.raises(TypeError) as e_info:
        decko_fixture.debug = "False"


"""
    Unit test:
    
        1. Func name: @decko.slower_than 
"""


@pytest.mark.parametrize("input_size",
                         [
                             10000000,
                             20000000,
                             30000000,
                         ]
                         )
@pytest.mark.parametrize("milliseconds",
                         [
                             100,
                             200,
                             300,
                         ]
                         )
def test_slower_than(input_size, milliseconds, decko_fixture):

    def raise_error(time_elapsed):
        raise ValueError(f"Took {time_elapsed} milliseconds")

    @decko_fixture.slower_than(milliseconds, callback=raise_error)
    def long_func(n):
        x = 0
        for i in range(n):
            x += i
        return x

    # Ideally these functions should take longer than 300 milliseconds to execute
    with pytest.raises(ValueError) as err:
        long_func(input_size)


def test_instance_data(decko_fixture):

    def setter(self, new_val):
        if new_val > 20:
            raise ValueError("Value set is greater than 20 ... ")

    @decko_fixture.instance_data(setter=setter)
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


def test_pure(decko_fixture):
    """
    The function below modifies the input array c:
    This should throw a value error.
    :return:
    """

    def raise_error(*args, **kwargs):
        print("yee")
        raise ValueError(f"Modified inputs: {args}, {kwargs}")

    @decko_fixture.pure(callback=raise_error)
    def input_output_what_how(a, b, c=[]):
        c.append(10)
        return c

    item = []

    # Should raise ValueError since 'item'
    # is being modified (values are added)
    with pytest.raises(ValueError) as error:
        input_output_what_how(10, 20, item)

    # this should also raise error
    with pytest.raises(ValueError) as error:
        input_output_what_how(10, 20)


def test_profile(decko_fixture):

    @decko_fixture.profile()
    def create_list(n):
        return list(range(n))

    for i in range(1, 10):
        create_list(1000 * i)

    decko_fixture.print_profile()


def test_freeze(decko_fixture):

    @decko_fixture.freeze
    class Dummy:
        def __init__(self):
            self.a = 1

    instance = Dummy()
    with pytest.raises(ImmutableError):
        instance.a = 200
