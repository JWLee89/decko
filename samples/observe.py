from src.decko import Decko


if __name__ == "__main__":

    dk = Decko(__name__)

    @dk.observe(properties=None, on_change=None)
    class DummyClass:
        def __init__(self, a, b):
            self.a = a
            self.b = b
            print(f"self.a: {self.a}, self.b: {self.b}")


    # Create instance of decorated class
    cls_instance = DummyClass(1, "two")

    print("dict --------")
    print(cls_instance.__dict__)

    # Update members
    print(cls_instance.b)
    cls_instance.b = "teeemo"

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