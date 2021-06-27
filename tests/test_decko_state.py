import pytest
from tests.common.fixtures import decko_fixture


def test_function_registration_state(decko_fixture):

    @decko_fixture.profile
    def create_list(n):
        return list(range(n))

    create_list(10)
    function_obj = decko_fixture.functions
    assert len(function_obj.keys()) == 1, "There should only be one registered function"
