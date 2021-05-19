class Props:
    """
    Dummy class for testing purity
    """
    def __init__(self, a, b):
        self.a = b
        self.b = b

    def __repr__(self):
        return f"a: {self.a}, b: {self.b}"

    def a_method(self):
        return self.a


class SampleSetterClass:

    class_member = 3

    def __init__(self, a):
        self.a = a

    def get_a(self):
        return self.a

    def set_a(self, val):
        self.a = val

    def __repr__(self):
        return f"self.a={self.a}"
