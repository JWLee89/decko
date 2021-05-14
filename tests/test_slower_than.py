from src.decko import Decko
import pytest

dk = Decko(__name__, debug=True)


@pytest.mark.parametrize("input_size",
    [
        100000,
        1000000,
        10000000,
    ]
)
@pytest.mark.parametrize("milliseconds",
    [
        1000,
        2000,
        3000,
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

    long_func(input_size)
