import sys
import os
from typing import Callable


class Yeezy:
    """
    Yeeeee ....
    Entry point of the application
    """
    def __init__(self,
                 root_path: str = None):

        #: Absolute path to the package on the filesystem. Used to look
        #: up resources contained in the package.
        self.root_path = root_path

        # Dictionary mapping function names to debug functions
        # E.g. "do_work" -- <Callable>
        self.debug_functions = {}

    def trace(self) -> Callable:
        """
        Used for running the trace function
        Example:
            yeezy.debug()
            def test():
                print("hello world")
        :rtype:
        """

    def __repr__(self) -> str:
        return "Yee ... yeezy :)"


