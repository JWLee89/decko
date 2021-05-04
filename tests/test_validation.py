from src.pojang.app import Pojang
import pytest

pj = Pojang(__name__)


def test_set_debug() -> None:
    """
    This should not trigger a type error, since we are
    setting debug to a boolean value
    """
    try:
        pj.debug = True
        pj.debug = False
    except TypeError:
        pytest.fail("This should not occur since .debug must "
                    "be set to boolean value.")
    assert not pj.debug, f"Expected: 'False', actual: {pj.debug}"


def test_invalid_set_debug() -> None:
    """
    This should trigger a type error, since we are
    setting debug to a string value
    """
    with pytest.raises(TypeError) as e_info:
        pj.debug = "False"
