import os
import pprint
from src.decko.helper.util import format_list_str

from src.decko.app import Decko

dk = Decko(__name__)


def get_python_files(root_folder):
    src_files = []
    for subdir, dirs, files in os.walk(root_folder):
        for file in files:
            # print os.path.join(subdir, file)
            filepath = subdir + os.sep + file

            if filepath.endswith(".py") and file != "__init__.py":
                src_files.append(filepath)
    return src_files


def test_initialization():
    """
    Test and ensure that unit test exists for each file.
    """

    # src folder must obviously exist
    src_path = '../src/decko'
    src_exists = os.path.exists(src_path)
    assert src_exists, "source folder does not exist"

    test_path = os.getcwd()
    src_files = get_python_files(src_path)
    test_files = get_python_files(test_path)

    # TODO: Create test script to ensure that number of unit tests
    # is equivalent to the number of script files.

    assert len(src_files) == len(test_files), \
        f"Missing unit tests.\n src:\n{format_list_str(src_files)}\n" \
        '-----------------------------------------------------\n' \
        f"Tests:\n{format_list_str(test_files)}"



