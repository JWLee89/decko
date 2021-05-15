import pytest

from src.decko.app import Decko

dk = Decko(__name__)


def test_immutable():
    """
    By default, raises value error when trying to set an
    internal property.
    :return:
    """

    @dk.immutable
    class Test:
        def __init__(self, test, cool):
            self.test = test
            self.cool = cool

        def do_test(self):
            print("Hello, test")

    instance = Test(2, 3)

    with pytest.raises(ValueError) as error:
        # Should raise value error since class properties
        # here are immutable
        instance.cool = 200


def test_immutable_with_observe():
    """
    The code above is built off observe,
    so the code below should run the same
    :return:
    :rtype:
    """
    def immutable(self, new_val):
        raise ValueError(f"Cannot set value: {new_val}")

    @dk.observe(setter=immutable)
    class Test:
        def __init__(self, test, cool):
            self.test = test
            self.cool = cool

    instance = Test(2, 3)
    with pytest.raises(ValueError) as error:
        instance.test = 1
