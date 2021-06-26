from src.decko.decorators import (
    log_trace
)
from tests.common.util import (
    cleanup_files
)


def test_log_trace():
    add_log, subtract_log = "file.log", "test.log"

    @log_trace(add_log, 20)
    def add(a, b):
        return a + b

    add(1, 2)

    @log_trace(subtract_log, 20)
    def subtract(a, b):
        return a - b

    subtract(10, 7)
    # assert cleanup_files(add_log, subtract_log), "Failed to clean up files properly."
