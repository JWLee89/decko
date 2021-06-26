import pytest
from src.decko.app import (
    Decko,
)


@pytest.fixture
def decko_fixture():
    return Decko(__name__)
