from src.yeezy.app import Yeezy

yee = Yeezy(__file__)


def test_decorator_registration():
    print(yee)
    print(__name__)
    assert yee is not None
