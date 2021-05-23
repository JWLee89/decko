from src.decko.helper.validation import (
    is_instancemethod,
)


def test_is_method():
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
