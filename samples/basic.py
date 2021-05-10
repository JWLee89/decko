from src.decko import Decko


if __name__ == "__main__":

    dk = Decko(__name__, debug=True)

    def print_list_size(size, **kwargs):
        print(f"Size of list is: {size}")

    def print_kwargs(*args, **kwargs):
        print(f"args: {args}, kwargs: {kwargs}")

    @dk.run_before([print_list_size, print_kwargs])
    @dk.profile
    def create_list(n):
        return list(range(n))

    for i in range(20):
        create_list(100000)

    # # print profiled result
    # dk.print_profile()

    # event triggered when original input is modified
    def catch_input_modification(arg_name, before, after):
        print(f"The argument: {arg_name} has been modified.\n"
              f"Before: {before} \n After: {after}")
        print("-" * 200)

    # @dk.pure(catch_input_modification)
    def create_list(n,
                    item=[]):
        item.append(n)
        return list(range(n))


    #

    dk.print_profile()
