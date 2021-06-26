from src.decko.debug import (
    log_trace
)
from tests.common.util import (
    cleanup_files
)


def test_log_trace():
    add_log, subtract_log, long_list_log = "file.log", "test.log", "create_long_list.log"

    @log_trace(add_log)
    def add(a, b, new_kwargs=20):
        return a + b

    add(1, 2)

    @log_trace(subtract_log)
    def subtract(a, b, kw=None):
        return a - b

    subtract(10, 7, kw=30)

    @log_trace(long_list_log)
    def create_long_list(a):
        return list(range(a))

    create_long_list(10000000)

    assert cleanup_files(add_log, subtract_log, long_list_log), \
        "Failed to clean up files properly."
