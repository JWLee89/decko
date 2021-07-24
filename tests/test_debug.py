import pytest
from src.decko.debug import (
    raise_error_if,
)


@pytest.mark.parametrize("test_case", [
    (2, 5, 5),
    (200, 500, 600)
])
def test_raise_errors_if(test_case):
    first_num, second_num, threshold_value = test_case

    def sum_greater_than_threshold(total_sum):
        return threshold_value < total_sum

    @raise_error_if(sum_greater_than_threshold)
    def add(a, b):
        return a + b

    with pytest.raises(RuntimeError):
        add(first_num, second_num)
