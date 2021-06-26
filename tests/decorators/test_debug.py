"""
@Author Jay Lee
Note: there is currently a lot of boilerplate.
Take some time to refactor all the unit tests by using fixtures and whatnot.
"""
import pytest
import typing as t

import src.decko.debug as debug



@pytest.mark.parametrize("iter_count", [
    4, 8, 12
])
def test_stopwatch(iter_count):
    time_elapsed_arr = []

    def callback(val):
        time_elapsed_arr.append(val)
        return val

    @debug.stopwatch(callback)
    def create_list(n):
        return list(range(n))

    for i in range(iter_count):
        create_list(1000000 * i)

    assert len(time_elapsed_arr) == iter_count, \
        f"Should have {len(time_elapsed_arr)} items"