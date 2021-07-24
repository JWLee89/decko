# Local imports
from .app import Decko

# Function decorators
from .decorators import (
    deckorator,
    execute_if,
    freeze,
    filter_by_output,
)

from .debug import (
    try_except,
    stopwatch,
    log_trace,
    slower_than,
    raise_error_if,
)


__version__ = "0.0.3.2"
PROJECT_NAME = "decko"
