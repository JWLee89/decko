import pytest

from src.decko.app import Decok
from src.decko.exceptions import MutatedReferenceError

dk = Decok(__name__)


def test_basic_pure():
    """
    This should raise an error, since it is mutating the original input
    """

    @dk.pure()
    def input_output_what_how(a, b, c=[]):
        c.append(10)
        return c

    item = []

    with pytest.raises(MutatedReferenceError):
        output = input_output_what_how(10, 20, item)

    # Even mutation of default variable should raise Error
    with pytest.raises(MutatedReferenceError):
        output = input_output_what_how(10, 20)
        # If this is not caught, "yee" will be an array of size 2.
        # yee = [10, 10]
        yee = input_output_what_how(10, 20)
        assert len(yee) == 3, "Side effect should result in array of size 3"
        # They should point to same object
        assert item is yee, "They don't point to the same object? What???"
