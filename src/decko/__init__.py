# Local imports
from .app import Decko

# Function decorators
from .decorators import (
    deckorator,
    execute_if,
    slower_than,
    freeze,
    filter_by_output,
    raise_error_if,
)

from .debug import (
    try_except,
    stopwatch,
    log_trace,
)


__version__ = "0.0.3.1"
PROJECT_NAME = "decko"
