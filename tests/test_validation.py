from src.yeezy.app import Yeezy
import pytest

yee = Yeezy(__name__)


def test_set_debug() -> None:
    """
    This should not trigger a type error, since we are
    setting debug to a boolean value
    """
    try:
        yee.debug = True
        yee.debug = False
    except TypeError:
        pytest.fail("This should not occur since .debug must "
                    "be set to boolean value.")
    assert not yee.debug, f"Expected: 'False', actual: {yee.debug}"


def test_invalid_set_debug() -> None:
    """
    This should trigger a type error, since we are
    setting debug to a string value
    """
    with pytest.raises(TypeError) as e_info:
        yee.debug = "False"
