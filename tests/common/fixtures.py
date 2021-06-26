import pytest
from src.decko.app import (
    Decko,
    deckorator,
)


@pytest.fixture
def decko_fixture():
    return Decko(__name__)


@pytest.fixture
def add_func(a: int, b: int) -> int:
    """
    Simple fixture for testing decorator
    Args:
        a: a number
        b: Another number

    Returns:
        The sum of two numbers
    """
    return a + b
