import sys


class Quantity:
    def __set_name__(self, owner, name):
        print("Name set:: ", name)
        self.name = name

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError(f"Must pass in value >= 0. "
                             f"Value passed: {value}")
        instance.__dict__[self.name] = value


class TimeProperty:
    """
    Basic descriptor of each class
    """

    def __init__(self) -> None:
        self.call_count = 0
        self.avg_run_time = 0
        self.max_run_time = 0
        self.min_run_time = sys.maxsize

    def __repr__(self) -> str:
        return f"Total call count: {self.call_count}, " \
               f"Average run time: {self.avg_run_time}, " \
               f"Max run time: {self.max_run_time}, " \
               f"Min run time: {self.min_run_time}"

    def update(self, time_elapsed):
        self.call_count += 1
        self.avg_run_time = (time_elapsed / self.call_count)
        self.max_run_time = max(time_elapsed, self.max_run_time)
        self.min_run_time = min(time_elapsed, self.min_run_time)


class TraceProperty(TimeProperty):
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


if __name__ == "__main__":
    a = TraceProperty()
    import time

    for i in range(50):
        start = time.time()
        item = list(range(100000))
        time_elapsed = time.time() - start
        a.update(time_elapsed)

    print(a)

