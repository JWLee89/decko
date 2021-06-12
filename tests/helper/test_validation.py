import pytest
import typing as t

from src.decko.helper.validation import (
    is_instancemethod,
    is_method,
)


@pytest.fixture(scope="module")
def sample_class_instance():
    class AClass:
        def __init__(self):
            pass

        def method(self):
            return "yaye"

        @classmethod
        def class_method(cls):
            return "yee"

        @staticmethod
        def static_method():
            return "naye"

    return AClass()


@pytest.fixture(scope="module")
def sample_function():
    def function():
        return function.__qualname__
    return function


def test_is_method(sample_class_instance, sample_function):
    function_is_not_method = not is_method(sample_function)
    meth = sample_class_instance.method
    bound_to: t.Type = getattr(meth, '__self__', None)
    print(bound_to)

    assert function_is_not_method, f"sample_function should not be a method: {bound_to}"


def test_is_instance_method():
    """
    Should only return true for functions that
    have a dot in the __qualname__
    """

    def a_function():
        return a_function.__name__

    class AClass:
        def __init__(self):
            pass

        def a_method(self):
            return "yaye"

        @classmethod
        def class_method(cls):
            return "yee"

        @staticmethod
        def static_method():
            return "naye"

    instance = AClass()
    error_msg = "Something is off"

    # Should yield false
    assert not is_instancemethod(instance.class_method), error_msg
    assert not is_instancemethod(AClass.static_method), error_msg
    assert not is_instancemethod(a_function), error_msg
    assert not is_instancemethod(10), error_msg
    assert not is_instancemethod((1, "str", 3)), error_msg

    # Only this should yield true
    assert is_instancemethod(instance.a_method), error_msg
    # Yes, function is an instance method believe it or not
    assert is_instancemethod(print), error_msg
