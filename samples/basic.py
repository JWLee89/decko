from src.pojang import Pojang

pj = Pojang(__name__, debug=True)

if __name__ == "__main__":

    def log_impurity(argument, before, after):
        print(f"Argument: {argument} modified. Before: {before}, after: {after}")

    def i_run_before(a, b, c, item):
        print(f"Run before func: {a}, {b}, {c}, {item}")

    @pj.run_before(i_run_before)
    @pj.pure(log_impurity)
    # @pj.profile
    def expensive_func(a,
                       b,
                       c=1000000,
                       item=[]):
        for i in range(100):
            temp_list = list(range(c))
            item.append(temp_list)

        a += 20
        b += a
        total = a + b
        return total

    class DummyClass:
        def __init__(self, item):
            self.item = item

        # @pj.pure(log_impurity)
        # @pj.profile
        def set_item(self, item):
            self.item = item

        def __repr__(self):
            return f'DummyClass: {self.item}'


    test = DummyClass(10)
    test.set_item(20)

    output = expensive_func(10, 20, 40)
    # pj.print_profile()
    print(pj.custom)


