import os
import pytest
from typing import Iterable, List

from src.decko.helper.util import format_list_str
from src.decko.app import Decko
from definitions import ROOT_DIR, TESTS_TO_EXCLUDE

dk = Decko(__name__)


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

def test_unit_test_count():
    """
    Test and ensure that unit test exists for each file.
    """

    # Paths
    test_path = f"{ROOT_DIR}/tests"
    src_path = f"{ROOT_DIR}/src/decko"

    # src folder must obviously exist
    src_exists = os.path.exists(src_path)
    assert src_exists, f"source folder does not exist in path: {src_path}"
    assert test_path, f"test folder does not exist in path: {test_path}"

    # Grab all the file names from src and test directory
    src_files = sorted(get_src_python_files(src_path, exclude=TESTS_TO_EXCLUDE))
    test_files = sorted(get_test_python_files(test_path))
    missing_unit_tests = []
    # Now, log each missing test file
    i, j = 0, 0
    while i < len(src_files) and j < len(test_files):
        src_file, test_file = src_files[i], test_files[j]
        if src_file == test_file:
            i += 1
            j += 1
        else:
            missing_unit_tests.append(src_file)
            i += 1

    # There should be a corresponding unit test for each python file
    assert len(missing_unit_tests) == 0, \
        f"Missing {len(missing_unit_tests)} unit test for the " \
        f"following files:\n{format_list_str(missing_unit_tests)}"


"""
    Unit test:

        1. Property name: debug
        E.g. self.debug
"""


def test_set_debug() -> None:
    """
    This should not trigger a type error, since we are
    setting debug to a boolean value
    """
    try:
        dk.debug = True
        dk.debug = False
    except TypeError:
        pytest.fail("This should not occur since .debug must "
                    "be set to boolean value.")
    assert not dk.debug, f"Expected: 'False', actual: {dk.debug}"


def test_invalid_set_debug() -> None:
    """
    This should trigger a type error, since we are
    setting debug to a string value
    """
    with pytest.raises(TypeError) as e_info:
        dk.debug = "False"


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
def test_slower_than(input_size, milliseconds):
    def raise_error(time_elapsed):
        raise ValueError(f"Took {time_elapsed} milliseconds")

    @dk.slower_than(milliseconds, callback=raise_error)
    def long_func(n):
        x = 0
        for i in range(n):
            x += i
        return x

    # Ideally these functions should take longer than 300 milliseconds to execute
    with pytest.raises(ValueError) as err:
        long_func(input_size)
