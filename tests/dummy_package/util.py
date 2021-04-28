from typing import List


def long_func(n: int = 1000000) -> List:
    """
    For testing large inputs
    :param n: The size of the list to be produced
    :return: A long list
    """
    return list(range(n))
