import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Files specified in this list
# are excluded from unit test requirements
# If not specified, a unit test file is required
TESTS_TO_EXCLUDE = ['exceptions.py']
