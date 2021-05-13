from src.decko import Decko
import pytest

dk = Decko(__name__)


@pytest.mark.parametrize("input_array_size",
    [10000,
    100000,
    10000000,
    ]
)
def test_slower_than(input_array_size):

    @dk.slower_than(100)
    def long_func(n):
        x = 0
        for i in range(n):
            x += i
        return x