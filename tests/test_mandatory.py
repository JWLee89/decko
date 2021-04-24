from src.yeezy.app import Yeezy

yee = Yeezy(__file__)


def test_decorator_registration():
    print(yee)
    assert yee is not None
