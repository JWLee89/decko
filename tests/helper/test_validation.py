from src.decko.helper.validation import (
    is_instance_method,
)


def test_is_method():
    """
    Should only return true for functions that
    have a dot in the __qualname__
    """
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

        @staticmethod
        def another_static():
            return "static"

    instance = AClass()
    error_msg = "Something is off"

    # Should yield false
    assert not is_instance_method(instance.class_method), error_msg
    assert not is_instance_method(AClass.static_method), error_msg
    assert not is_instance_method(AClass.another_static), error_msg
    assert not is_instance_method(print), error_msg
    assert not is_instance_method(10), error_msg
    assert not is_instance_method((1, "str", 3)), error_msg

    # Only this should yield true
    assert is_instance_method(instance.a_method), error_msg
