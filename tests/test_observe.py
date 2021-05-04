import pytest

from src.pojang.app import Pojang

pj = Pojang(__name__)


def test_invalid_input():
    with pytest.raises(ValueError) as e_info:
        @pj.observe(['test', 10, 20, 30])
        class Test:
            def __init__(self, test, cool):
                self.test = test
                self.cool = cool

        # Must pass in a flat array of strings
        @pj.observe(['test', ['10', '20', '30']])
        class Test:
            def __init__(self, test, cool):
                self.test = test
                self.cool = cool

        # Properties ['10', '20', '30'] don't exist in Test()
        @pj.observe(['test', '10', '20', '30'])
        class Test:
            def __init__(self, test, cool):
                self.test = test
                self.cool = cool


def test_valid_input():
    try:
        array_input = ['test']

        # this should be okay
        @pj.observe(array_input)
        class Test:
            def __init__(self, test, cool):
                self.test = test
                self.cool = cool

        # test = Test()
        # observed_test = yee.observe(['cool'])(test)

    except ValueError:
        pytest.fail("The observable list contains invalid properties")
