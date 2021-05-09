import sys
import json
from typing import Callable
import abc


class Quantity:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError(f"Must pass in value >= 0. "
                             f"Value passed: {value}")
        instance.__dict__[self.name] = value


def ComplexHandler(Obj):
    if hasattr(Obj, 'jsonable'):
        return Obj.jsonable()
    else:
        raise TypeError(f'Object of type {type(Obj)} with value of '
                        f'{repr(Obj)} is not JSON serializable')


class Statistics(abc.ABC):
    """
    Base class for creating statistics
    """
    def __init__(self, func: Callable) -> None:
        self.func = func
        self.call_count = 0
        self._stats = []    # TODO: Maybe implement statistics update like a chain

    def merge(self, statistics):
        properties = self.__dict__.keys()
        for key, value in statistics.__dict__:
            if key not in properties:
                setattr(self, key, value)

    def __repr__(self) -> str:
        return json.dumps(self.__dict__, indent=4)


class TraceStatistics(Statistics):
    def __init__(self, func) -> None:
        super().__init__(func)


class TimeStatistics(Statistics):
    """
    Basic descriptor of each class
    """

    def __init__(self, func) -> None:
        super().__init__(func)
        self.avg_run_time = 0
        self.max_run_time = 0
        self.min_run_time = sys.maxsize

    def __repr__(self) -> str:
        # return json.dumps(self.__dict__, indent=4)
        return f"Total call count: {self.call_count}, " \
               f"Average run time: {self.avg_run_time}, " \
               f"Max run time: {self.max_run_time}, " \
               f"Min run time: {self.min_run_time}"

    def update(self, time_elapsed, *args, **kwargs):
        self.call_count += 1
        self.avg_run_time = (time_elapsed / self.call_count)
        self.max_run_time = max(time_elapsed, self.max_run_time)
        self.min_run_time = min(time_elapsed, self.min_run_time)


class Test:
    @staticmethod
    def print_this():
        print("yeetoozzz")


def create_long_list(n = 1000000, name="test"):
    print("create long list")
    return list(range(n)), name


class TraceStatistics(TimeStatistics):
    """
    The information displayed when trace is applied
    """
    def __init__(self, io_truncate_size=200):
        super().__init__()
        self.io_truncate_size = io_truncate_size
        self.inputs = []
        self.outputs = []

    def __repr__(self):
        prev_str = super().__repr__()
        return prev_str

    def update(self, properties):
        if "time_elapsed" in properties:
            super().update(properties['time_elapsed'])
        for key in properties.key():
            setattr(self, key, properties[key])


if __name__ == "__main__":
    a = TraceStatistics()
    import time

    for i in range(50):
        start = time.time()
        item = list(range(100000))
        time_elapsed = time.time() - start
        a.update(time_elapsed)

    print(a)

