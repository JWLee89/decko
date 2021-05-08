from src.pojang import Pojang
import pstats

pj = Pojang(__name__)

if __name__ == "__main__":

    @pj.pure
    def expensive_func(a,
                       b,
                       c=1000000,
                       item=[]):
        total = 0
        for i in range(100):
            temp_list = list(range(c))
            item.append(temp_list)

        a += 20
        b += a
        total = a + b
        return total


    output = expensive_func(10, 20)

    # stats = pstats.Stats(pj._profiler).sort_stats('ncalls')
    # stats.print_stats()
