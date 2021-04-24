from src.yeezy.app import Yeezy
from typing import List

yee = Yeezy(__file__)


def test_decorator_registration():
    print(yee)
    print(__name__)
    assert yee is not None


def test_class_side_effect_detection():
    class Test:
        def __init__(self, ass):
            self.yee = [1, 2, 3, 4, 5]

        def do_side_effect(self, a: List):
            a.append(10)

    yee.profile()
    yee
