import pytest
from src.decko.debug import (
    raise_error_if,
)


@pytest.mark.parametrize("threshold_value", [
    5,
    600
])
@pytest.mark.parametrize("a_and_b", [
    (2, 5),
    (200, 500)
])
def test_raise_errors_if(threshold_value, a_and_b):
    first_num, second_num = a_and_b

    def sum_greater_than_threshold(total_sum):
        print(f"threshold: {threshold_value}, sum: {total_sum}")
        return threshold_value < total_sum

    @raise_error_if(sum_greater_than_threshold)
    def add(a, b):
        return a + b

    with pytest.raises(RuntimeError):
        add(first_num, second_num)
