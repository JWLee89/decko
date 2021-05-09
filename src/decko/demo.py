from app import Decko


def simple_demo():
    import torch

    yee = Decko(__name__, debug=True, log_path=None)

    # This should register all functions inside of class Test()
    # @yee.time
    class Test:
        def __init__(self):
            self.test = [1, 2, 3]

        def mutate(self, num):
            self.test.append(num)

        def print_something(self, test):
            print(test)

        # @yee.trace()
        @yee.stopwatch
        def create_long_list(self, n=1000000, name="test"):
            return torch.tensor(range(n))

    @yee.stopwatch
    def create_long_list(n=1000000, name="test"):
        return list(range(n)), name

    # Some class
    tom = Test()

    # Another create long list
    def bonk(*args, **kwargs):
        print(f"Bonk: {args}, {kwargs}")

    # We can also add decorators dynamically
    # TODO: Right now, we lose the computational information,
    # so we need to find a way to preserve this
    create_long_list = yee.before(bonk)

    for i in range(20):
        tom.create_long_list(i)
        create_long_list(i)

    print("-" * 100)

    # Profile and gather information
    yee.analyze()


if __name__ == "__main__":
    simple_demo()
