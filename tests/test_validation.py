from src.decko.app import Decok
import pytest

dk = Decok(__name__)


def test_set_debug() -> None:
    """
    This should not trigger a type error, since we are
    setting debug to a boolean value
    """
    try:
        dk.debug = True
        dk.debug = False
    except TypeError:
        pytest.fail("This should not occur since .debug must "
                    "be set to boolean value.")
    assert not dk.debug, f"Expected: 'False', actual: {dk.debug}"


def test_invalid_set_debug() -> None:
    """
    This should trigger a type error, since we are
    setting debug to a string value
    """
    with pytest.raises(TypeError) as e_info:
        dk.debug = "False"
