from src.decko import Decko


if __name__ == "__main__":

    dk = Decko(__name__, debug=True, log_path="test.logger")

    # def print_list_size(size, **kwargs):
    #     print(f"Size of list is: {size}")
    #
    # def print_kwargs(*args, **kwargs):
    #     print(f"args: {args}, kwargs: {kwargs}")
    #
    # @dk.run_before([print_list_size, print_kwargs])
    # @dk.profile
    # def create_list(n):
    #     return list(range(n))
    #
    # for i in range(20):
    #     create_list(100000)
    #
    # # # print profiled result
    # # dk.print_profile()

    # event triggered when original input is modified
    # def catch_input_modification(arg_name, before, after):
    #     print(f"The argument: {arg_name} has been modified.\n"
    #           f"Before: {before} \n After: {after}")
    #     print("-" * 200)
    #
    # # @dk.pure(catch_input_modification)
    # def create_list(n,
    #                 item=[]):
    #     item.append(n)
    #     return list(range(n))
    #
    # dk.print_profile()

    def callback(*args):
        print(f"called: {args}")

    @dk.trace
    class Test:
        def __init__(self, a):
            self.a = a

        def method(self):
            # self.a = 2
            return self.a

        def __repr__(self):
            return f"self.a={self.a}"

    class Cow:
        pass

    @dk.pure()
    def print_something(a):
        print(a)

    test = Test(1)
    test.method()
    print_something(10000)

    print(dk.functions)
