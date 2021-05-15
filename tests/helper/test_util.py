import pytest
from typing import Tuple, Any

from src.decko.helper.util import (
    create_instance,
)


class DummyClass:
    """
    Dummy class for testing the following functions
        - test_create_instance
        - test_create_instance_with_args
    """
    def __init__(self, a, b, c=(1, )):
        self.a = a
        self.b = b
        self.c = c

    def __repr__(self) -> str:
        return f"a: {self.a}, b: {self.b}, c: {self.c}"


def test_create_instance():
    class EmptyClass:
        pass

    class ComplexTuple(tuple):
        def __init__(self, *args):
            super().__init__(*args)


    instances = []
    instances.append((create_instance(EmptyClass), EmptyClass))
    instances.append((create_instance(DummyClass), DummyClass))
    instances.append((create_instance(ComplexTuple), ComplexTuple))

    for instance, Type in instances:
        assert isinstance(instance, Type), f"Instance of {Type.__name__} is not of type: {Type}"


@pytest.mark.parametrize("a_b_c",
                         [
                             (1, 2, 3),
                             ('test', 1.234, print),
                             ((1, 2, 5), "donk", [print, isinstance])
                         ]
                         )
def test_create_instance_with_args(a_b_c: Tuple[Any, Any, Any]):
    # This should create class as follows
    # instance = DummyClass(1, 2, 3)
    a, b, c = a_b_c
    instance = create_instance(DummyClass, a, b, c)
    assert instance.a == a and instance.b == b and instance.c == c, \
        f"Instance {instance} should have properties: a:{a}, b:{b}, c:{c}"
