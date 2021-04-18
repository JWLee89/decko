import time
from typing import List


class TimeComputer:
    """
    Class for running experiments for computing the average time taken
    to perform computation over a series of N runs. Example:

    time_elapsed_ms = []
    for i in range(100):
        with TimeComputer(time_elapsed_ms) as tc:
            # Run experiment here
            items = list(range(100000))
     print(f"Avg time elapsed: {TimeComputer.compute_avg_time(time_elapsed_ms, unit=TimeComputer.Units.MS)}")
    """
    class Units:
        MS = 'milliseconds'

    def __init__(self, accumulated_time: List) -> None:
        if not isinstance(accumulated_time, list):
            raise TypeError(f"Accumulated_time must be a list. "
                            f"Passed in type: {type(accumulated_time)}")
        self.accumulated_time = accumulated_time

    def __enter__(self) -> None:
        self.start_time = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        time_elapsed = time.time() - self.start_time
        self.accumulated_time.append(time_elapsed)

    @staticmethod
    def compute_avg_time(time_list: List, unit: str = None) -> float:
        avg_time = sum(time_list) / len(time_list)
        if unit == TimeComputer.Units.MS:
            avg_time *= 1000
        return avg_time

