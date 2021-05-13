from src.decko import Decko
import pytest

dk = Decko(__name__, debug=True)


@pytest.mark.parametrize("input_size",
    [
        100000,
        10000000,
        100000000,
    ]
)
def test_slower_than(input_size):

    def raise_error(time_elapsed):
        raise ValueError(f"Took {time_elapsed} milliseconds")

    @dk.slower_than(1, callback=raise_error)
    def long_func(n):
        x = 0
        for i in range(n):
            x += i
        return x

    long_func(input_size)
