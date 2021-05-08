from src.pojang import Pojang
import pstats

pj = Pojang(__name__)

if __name__ == "__main__":

    def detect_error(argument, before, after):
        print(f"Argument: {argument} modified. Before: {before}")

    def i_run_before(a, b, c, item):
        print(f"Run before func: {a}, {b}, {c}, {item}")

    @pj.run_before(i_run_before)
    @pj.pure(detect_error)
    @pj.profile
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

    output = expensive_func(10, 20, 10000)

    stats = pstats.Stats(pj._profiler).sort_stats('ncalls')
    stats.print_stats()
