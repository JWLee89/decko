from src.decko import Decko

if __name__ == "__main__":
    dk = Decko(__name__)


    @dk.freeze
    @dk.stopwatch
    @dk.trace
    class DummyClass:
        def __init__(self, a):
            self.a = a

        @dk.profile
        def get_a(self):
            for i in range(10000):
                lst = list(range(1000))
            return self.a


    test = DummyClass(1)
    for i in range(10):
        print(f"test.a is {test.get_a()}")
    dk.print_profile()

    try:
        test.a = 10
    except:
        print("Yee ... cannot set attributes of frozen class")