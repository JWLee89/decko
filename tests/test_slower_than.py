from src.decko import Decko
import pytest

dk = Decko(__name__, debug=True)


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
