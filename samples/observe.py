from src.decko import Decko


if __name__ == "__main__":

    dk = Decko(__name__)

    @dk.observe(filter_predicate=None)
    class DummyClass:
        def __init__(self, a, b):
            # Properties are already initialized at this point
            self.a = a
            self.b = b
            self.c = []
            print(f"I am called twice: self.a: {self.a}, self.b: {self.b}, self._c: {self.c}")

    class PropertyClass:
        def __init__(self, a, b):
            self._a = a
            self._b = b
            self._c = []
            print(f"I am called twice: self.a: {self.a}, self.b: {self.b}, self._c: {self.c}")

        @property
        def a(self):
            return self._a

        @a.setter
        def a(self, new_val):
            print(f"key: , val: {new_val}")
            self._a = new_val

        @property
        def b(self):
            return self._b

        @b.setter
        def b(self, b):
            print(f"key: , val: {b}")
            self._b = b

        @property
        def c(self):
            return self._c

        @c.setter
        def c(self, c):
            print(f"key: , val: {c}")
            self._c = c

    # Create instance of decorated class
    cls_instance = DummyClass(1, "two")
    cls_instance.a = 10
    cls_instance.b = "C"
    print(cls_instance.__dict__)
    print("-" * 100)

    cls_instance = PropertyClass(1, "two")
    print(cls_instance.__dict__)

    @dk.observe()
    class Frozen:
        def __init__(self, a, b):
            self.a = a
            self.b = b

        def __repr__(self):
            return f"a:{self.a}, b: {self.b}"

    let_it_go = Frozen("one", "two")

    # Invalid
    let_it_go.b = 20
    # Also invalid
    # let_it_go.do_something = print
    print(let_it_go)
