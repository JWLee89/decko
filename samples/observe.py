from src.decko import Decko


if __name__ == "__main__":

    dk = Decko(__name__)

    @dk.observe(filter_predicate=None)
    class DummyClass:
        def __init__(self, a, b):
            self.a = a
            self.b = b
            self.c = []
            print(f"self.a: {self.a}, self.b: {self.b}, self._c: {self.c}")


    # Create instance of decorated class
    cls_instance = DummyClass(1, "two")

    # Update members
    cls_instance.b = "teeemo"

    # Event fires when updated
    cls_instance.c.append(10)
    cls_instance.c = 10


    # class Test:
    #     def __init__(self, a):
    #         self.__a = a
    #
    #     @property
    #     def a(self):
    #         print("a")
    #         return self.__a
    #
    #     @a.setter
    #     def a(self, v):
    #         print("yee")
    #         self.__a = v
    #
    # troll = Test(1)
    # troll.a = 100
    #
    # print(Test.__dict__)