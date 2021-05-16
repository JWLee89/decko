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